import { useEffect, useState } from "react";
import { api } from "./api";

function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [ingestingId, setIngestingId] = useState(null);

  const [question, setQuestion] = useState("");
  const [selectedDocument, setSelectedDocument] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assetUrls, setAssetUrls] = useState({});

  const fetchDocuments = async () => {
    try {
      const response = await api.get("/documents");
      console.log(response.data);
      setDocuments(response.data);
    } catch (error) {
      console.error(error);
      alert("Failed to load documents");
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
      alert("Document fully ingested!");
    } catch (error) {
      console.error(error);
      alert("Ingestion failed");
    } finally {
      setIngestingId(null);
    }
  };

  const uploadDocument = async () => {
    if (!file) {
      alert("Select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post("/documents/upload", formData);
      alert("Document uploaded successfully!");
      setFile(null);
      fetchDocuments();
    } catch (error) {
      console.error(error);
      alert("Upload failed");
    }
  };

  const loadAssetUrl = async (assetId) => {
    if (assetUrls[assetId]) return;

    try {
      const response = await api.get(`/assets/${assetId}`);

      setAssetUrls((prev) => ({
        ...prev,
        [assetId]: response.data.image_url,
      }));
    } catch (error) {
      console.error("Failed to load asset URL:", error);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Enter a question");
      return;
    }

    if (!selectedDocument) {
      alert("Select a document");
      return;
    }

    try {
      setLoading(true);

      const response = await api.post("/chat", null, {
        params: {
          question,
          top_k: 5,
          document_id: [selectedDocument],
        },
      });
      console.log(response.data);

      setAnswer(response.data.answer);
      setSources(response.data.sources);
      response.data.sources.forEach((source) => {
        if (source.asset_id) {
          loadAssetUrl(source.asset_id);
        }
      });
    } catch (error) {
      console.error(error);
      alert("Failed to get answer");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div style={{ maxWidth: "1000px", margin: "40px auto" }}>
      <h1>HPC Multimodal RAG Analyzer</h1>

      <hr />

      <h2>Upload Document</h2>

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />

      <button onClick={uploadDocument}>Upload</button>

      <hr />

      <h2>Documents</h2>

      {documents.length === 0 ? (
        <p>No documents uploaded yet.</p>
      ) : (
        <table border="1" cellPadding="8" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Type</th>
              <th>Status</th>
              <th>Chunks</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.filename}</td>
                <td>{doc.file_type}</td>
                <td>{doc.status}</td>
                <td>{doc.chunk_count}</td>
                <td>{new Date(doc.created_at).toLocaleString()}</td>
                <td>
                  <button
                    onClick={() => processDocument(doc.id)}
                    disabled={
                      doc.status === "ready" ||
                      doc.status === "processing" ||
                      ingestingId === doc.id
                    }
                  >
                    {ingestingId === doc.id
                      ? "Ingesting..."
                      : doc.status === "ready"
                        ? "Ingested"
                        : "Ingest"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <hr />

      <h2>Ask Questions</h2>
      <select
        value={selectedDocument}
        onChange={(e) => setSelectedDocument(e.target.value)}
      >
        <option value="">Select document</option>

        {documents.map((doc) => (
          <option key={doc.id} value={doc.id}>
            {doc.filename}
          </option>
        ))}
      </select>
      <br />

      <input
        type="text"
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button onClick={askQuestion}>Ask</button>
      <hr />

      <h3>Answer</h3>

      {answer && (
        <div>
          <p>{answer}</p>
          {sources.length > 0 && (
            <div>
              <h3>Sources</h3>

              {sources.map((source, index) => (
                <div key={index}>
                  <p>
                    <strong>Source {index + 1}</strong> — Page{" "}
                    {source.page_number} | {source.source_type}
                  </p>

                  <p>{source.preview}</p>

                  {source.asset_id && assetUrls[source.asset_id] && (
                    <img
                      src={assetUrls[source.asset_id]}
                      alt="Retrieved source"
                      width="300"
                    />
                  )}

                  <hr />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
