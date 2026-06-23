import { useState } from "react";
import api from "./api";

function App() {
  const[file, setFile] = useState(null)

  const uploadDocument = async () => {
    if (!file) {
      alert("Select a file first!!")
      return
    }

    const formData = new FormData();
    formData.append("file", file)

    try {
      const response = await api.post("/documents/upload")
      console.log(response.data)
      alert("Document uploaded successfully!")
    } catch (error) {
      console.log(error)
      alert("Upload failed")
    }
  };
  return (
    <div style={{ maxWidth: "1000px", margin: "40px auto" }}>
      <h1>HPC Multimodal RAG Analyzer</h1>
      <hr />

      <h2>Upload Document</h2>
      <input type="file"
      onChange={(e) => setFile(e.target.files[0])} />

      <button onClick={uploadDocument}>Upload</button>

      <hr />
      <h2>Documents</h2>
      <hr />
      <h2>Ask Questions</h2>
    </div>
  );
}

export default App;