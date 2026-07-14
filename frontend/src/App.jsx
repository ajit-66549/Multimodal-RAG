import { useState, useEffect, useMemo } from "react";
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
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assetUrls, setAssetUrls] = useState({});

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

      await api.post(`/documents/${documentId}/process`);
      await api.post(`/documents/${documentId}/embed`);

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
    if (!question.trim()) {
      showNotice("error", "Enter a question before asking the assistant.");
      return;
    }

    if (!selectedDocument) {
      showNotice("error", "Select a ready document to ground the answer.");
      return;
    }

    try {
      setLoading(true);
      setAnswer("");
      setSources([]);

      const response = await api.post("/chat", null, {
        params: { question, top_k: 5, document_id: [selectedDocument] },
      });

      setAnswer(response.data.answer);

      setSources(response.data.sources || []);
      (response.data.sources || []).forEach((source) => {
        if (source.asset_id) loadAssetUrl(source.asset_id);
      });
    } catch (error) {
      console.error(error);
      showNotice("error", "Failed to generate an answer. Please try again.");
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    // Fetch once on mount so the dashboard opens with the current document pipeline.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);



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

      <section className="content-grid">
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

        <div className="panel" id="ask">
          <div className="panel-heading">
            <p className="eyebrow">Step 3</p>
            <h2>Ask with evidence</h2>
          </div>
          <select value={selectedDocument} onChange={(e) => setSelectedDocument(e.target.value)}>
            <option value="">Select a ready document</option>
            {readyDocuments.map((doc) => (
              <option key={doc.id} value={doc.id}>{doc.filename}</option>
              ))}
          </select>
          <textarea
            placeholder="Ask about figures, tables, procedures, or document details..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows="4"
          />
          <button className="button button-primary" onClick={askQuestion} disabled={loading}>
            {loading ? "Searching evidence..." : "Ask assistant"}
          </button>
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

      <section className="panel answer-panel">
        <div className="panel-heading">
          <p className="eyebrow">Result</p>
          <h2>Answer</h2>
        </div>
        {!answer && <div className="empty-state">Your grounded answer and retrieved source cards will appear here.</div>}
        {answer && <p className="answer-text">{answer}</p>}
        {sources.length > 0 && (
          <div className="source-grid">
            {sources.map((source, index) => (
              <article className="source-card" key={`${source.asset_id || source.page_number}-${index}`}>
                <div className="source-meta">Source {index + 1} · Page {source.page_number} · {source.source_type}</div>
                <p>{source.preview}</p>
                {source.asset_id && assetUrls[source.asset_id] && <img src={assetUrls[source.asset_id]} alt="Retrieved visual source" />}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

export default App;