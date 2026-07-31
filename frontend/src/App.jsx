import { useState, useEffect, useMemo, useRef } from "react";
import { api } from "./api.js"

const statusLabels = {
  ready: "Ready",
  processing: "Processing",
  uploaded: "Uploaded",
  failed: "Needs attention",
};

function StatusBadge({ status }) {
  const normalized = status || "uploaded";
  return (
    <span className={`status-badge status-${normalized}`}>
      <span className="status-dot" />
      {statusLabels[normalized] || normalized}
    </span>
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [ingestingId, setIngestingId] = useState(null);
  const [notice, setNotice] = useState(null);

  const [question, setQuestion] = useState("");
  const [selectedDocument, setSelectedDocument] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assetUrls, setAssetUrls] = useState({});
  const conversationEndRef = useRef(null);

  const readyDocuments = useMemo(
    () => documents.filter((document) => document.status === "ready"),
    [documents],
  );

  const totalChunks = useMemo(
    () => documents.reduce((sum, document) => sum + (document.chunk_count || 0), 0),
    [documents],
  );

  const showNotice = (type, message) => {
    setNotice({ type, message });
    window.setTimeout(() => setNotice(null), 4500);
  };

  const fetchDocuments = async () => {
    try {
      const response = await api.get("/documents");
      console.log(response.data);
      setDocuments(response.data);
    } catch (error) {
      console.error(error);
      showNotice("error", "Failed to load documents. Check that the backend is running.");
    }
  };

  const processDocument = async (documentId) => {
    try {
      setIngestingId(documentId);

      const doc = documents.find((item) => item.id === documentId);

      await api.post(`/document/${documentId}/process`);
      await api.post(`/document/${documentId}/embed`);

      if (doc?.file_type === ".pdf") {
        await api.post(`/documents/${documentId}/extract-images`);
        await api.post(`/documents/${documentId}/ocr-assets`);
        await api.post(`/documents/${documentId}/embed-assets`);
      }

      await fetchDocuments();
      showNotice("success", "Document is ready for multimodal Q&A.");
    } catch (error) {
      console.error(error);
      showNotice("error", "Ingestion failed. Please retry or inspect backend logs.");
    } finally {
      setIngestingId(null);
    }
  };

  const uploadDocument = async () => {
    if (!file) {
      alert("Select a file first.");
      showNotice("error", "Select a PDF, CSV, or image-backed document first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post("/documents/upload", formData);
      showNotice("success", "Document uploaded. Run ingestion to make it searchable.");
      setFile(null);
      document.getElementById("file-upload").value = "";
      fetchDocuments();
    } catch (error) {
      console.error(error);
      showNotice("error", "Upload failed. Please try another file.");
    }
  };

  const loadAssetUrl = async (assetId) => {
    if (assetUrls[assetId]) return;

    try {
      const response = await api.get(`/assets/${assetId}`);

      setAssetUrls((prev) => ({ ...prev, [assetId]: response.data.image_url }));
    } catch (error) {
      console.error("Failed to load asset URL:", error);
    }
  };

  const askQuestion = async () => {
    const submittedQuestion = question.trim();
    if (!submittedQuestion) {
      showNotice("error", "Enter a question before asking the assistant.");
      return;
    }

    if (!selectedDocument) {
      showNotice("error", "Select a ready document to ground the answer.");
      return;
    }

    try {
      setLoading(true);
      setQuestion("");
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "user", content: submittedQuestion },
      ]);

      const response = await api.post("/chat", null, {
        params: { question: submittedQuestion, top_k: 5, document_id: [selectedDocument] },
      });

      const responseSources = response.data.sources || [];
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.data.answer,
          sources: responseSources,
        },
      ]);
      responseSources.forEach((source) => {
        if (source.asset_id) loadAssetUrl(source.asset_id);
      });
    } catch (error) {
      console.error(error);
      showNotice("error", "Failed to generate an answer. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleComposerKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!loading) askQuestion();
    }
  };


  useEffect(() => {
    // Fetch once on mount so the dashboard opens with the current document pipeline.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, loading]);



  return (
    <main className="app-shell">
      {notice && <div className={`toast toast-${notice.type}`}>{notice.message}</div>}

      <section className="hero-card">
        <div className="hero-content">
          <p className="eyebrow">Multimodal retrieval workspace</p>
          <h1>HPC Multimodal RAG Analyzer</h1>
          <p className="hero-copy">
            Upload technical documents, extract text and visual evidence, then ask grounded
            questions with traceable citations from your knowledge base.
          </p>
          <div className="hero-actions">
            <a className="primary-link" href="#ask">Ask a question</a>
            <a className="secondary-link" href="#documents">Review documents</a>
          </div>
        </div>
        <div className="metrics-grid" aria-label="Workspace summary">
          <div>
            <strong>{documents.length}</strong>
            <span>Documents</span>
          </div>
          <div>
            <strong>{readyDocuments.length}</strong>
            <span>Ready</span>
          </div>
          <div>
            <strong>{totalChunks}</strong>
            <span>Chunks indexed</span>
          </div>
        </div>
      </section>

      <section className="chat-panel" id="ask">
        <header className="chat-header">
          <div className="assistant-identity">
            <span className="assistant-avatar" aria-hidden="true">✦</span>
            <div>
              <h2>Research assistant</h2>
              <span className="online-label"><span /> Ready to search your documents</span>
            </div>
          </div>
          <select
            className="document-selector"
            aria-label="Document to search"
            value={selectedDocument}
            onChange={(e) => setSelectedDocument(e.target.value)}
          >
            <option value="">Select a ready document</option>
            {readyDocuments.map((doc) => (
              <option key={doc.id} value={doc.id}>{doc.filename}</option>
            ))}
          </select>
        </header>

        <div className="conversation" aria-live="polite">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <span className="welcome-icon">✦</span>
              <h2>What would you like to know?</h2>
              <p>Select a ready document, then ask about its text, tables, figures, or procedures.</p>
              <div className="prompt-suggestions">
                {["Summarize the key findings", "What do the figures show?", "List the main recommendations"].map((prompt) => (
                  <button key={prompt} type="button" onClick={() => setQuestion(prompt)}>{prompt}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((message) => (
            <article className={`message message-${message.role}`} key={message.id}>
              <div className="message-avatar" aria-hidden="true">{message.role === "assistant" ? "✦" : "You"}</div>
              <div className="message-body">
                <span className="message-author">{message.role === "assistant" ? "Research assistant" : "You"}</span>
                <p>{message.content}</p>
                {message.sources?.length > 0 && (
                  <details className="sources-details">
                    <summary>{message.sources.length} sources used</summary>
                    <div className="source-grid">
                      {message.sources.map((source, index) => (
                        <article className="source-card" key={`${message.id}-${source.asset_id || source.page_number}-${index}`}>
                          <div className="source-meta">Source {index + 1} · Page {source.page_number} · {source.source_type}</div>
                          <p>{source.preview}</p>
                          {source.asset_id && assetUrls[source.asset_id] && <img src={assetUrls[source.asset_id]} alt="Retrieved visual source" />}
                        </article>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </article>
          ))}
          {loading && (
            <article className="message message-assistant">
              <div className="message-avatar" aria-hidden="true">✦</div>
              <div className="message-body"><span className="message-author">Research assistant</span><div className="typing"><span /><span /><span /></div></div>
            </article>
          )}
          <div ref={conversationEndRef} />
        </div>

        <div className="composer-wrap">
          <div className="composer">
            <textarea
              aria-label="Message the research assistant"
              placeholder={selectedDocument ? "Message the research assistant…" : "Select a ready document to begin…"}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleComposerKeyDown}
              rows="1"
            />
            <button className="send-button" aria-label="Send message" onClick={askQuestion} disabled={loading || !question.trim() || !selectedDocument}>↑</button>
          </div>
          <small>Answers are grounded in the selected document. Press Enter to send · Shift + Enter for a new line.</small>
        </div>
      </section>

      <section className="content-grid workspace-grid">
        <div className="panel upload-panel">
          <div className="panel-heading">
            <p className="eyebrow">Step 1</p>
            <h2>Upload knowledge</h2>
          </div>
          <label className="dropzone" htmlFor="file-upload">
            <span className="upload-icon">↑</span>
            <strong>{file ? file.name : "Drop in a document"}</strong>
            <small>PDFs unlock image extraction, OCR, and asset search.</small>
            <input id="file-upload" type="file" onChange={(e) => setFile(e.target.files[0])} />
          </label>
          <button className="button button-primary" onClick={uploadDocument}>Upload document</button>
        </div>

        <div className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Workspace</p>
            <h2>Chat tips</h2>
          </div>
          <ul className="tips-list">
            <li>Ask follow-up questions without losing earlier answers.</li>
            <li>Open the source list beneath any response to inspect its evidence.</li>
            <li>Choose a different document from the conversation header at any time.</li>
          </ul>
        </div>
      </section>

      <section className="panel" id="documents">
        <div className="panel-heading split-heading">
          <div>
            <p className="eyebrow">Step 2</p>
            <h2>Document pipeline</h2>
          </div>
          <button className="button button-ghost" onClick={fetchDocuments}>Refresh</button>
        </div>

        {documents.length === 0 ? (
          <div className="empty-state">No documents yet. Upload one to start building your RAG index.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Filename</th><th>Type</th><th>Status</th><th>Chunks</th><th>Created</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td><strong>{doc.filename}</strong></td>
                    <td><span className="file-pill">{doc.file_type || "file"}</span></td>
                    <td><StatusBadge status={doc.status} /></td>
                    <td>{doc.chunk_count || 0}</td>
                    <td>{new Date(doc.created_at).toLocaleString()}</td>
                    <td>
                      <button className="button button-small" onClick={() => processDocument(doc.id)} disabled={doc.status === "ready" || doc.status === "processing" || ingestingId === doc.id}>
                        {ingestingId === doc.id ? "Ingesting..." : doc.status === "ready" ? "Ingested" : "Ingest"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

    </main>
  )
}

export default App;
