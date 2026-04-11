import { useMemo, useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/authService";

const formatFileSize = (bytes) => {
  if (!bytes) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let value = bytes;

  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }

  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

const getFileIcon = (fileType) => {
  const icons = {
    PDF: "📄",
    DOCX: "📝",
    DOC: "📝",
    XLSX: "📊",
    XLS: "📊",
    TXT: "📃",
    JPG: "🖼️",
    PNG: "🖼️",
  };
  return icons[fileType] || "📦";
};

const Dashboard = () => {
  const { user, token, logout } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [selectedChunkFile, setSelectedChunkFile] = useState(null);
  const [chunkViewerLoading, setChunkViewerLoading] = useState(false);
  const [chunkViewerError, setChunkViewerError] = useState(null);
  const [semanticChunks, setSemanticChunks] = useState([]);

  // Fetch files on mount
  useEffect(() => {
    fetchFiles();
  }, [token]);

  // Filter documents based on search and type
  useEffect(() => {
    let filtered = documents;

    if (searchTerm) {
      filtered = filtered.filter((doc) =>
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedFilter !== "all") {
      filtered = filtered.filter(
        (doc) => doc.file_type.toLowerCase() === selectedFilter.toLowerCase()
      );
    }

    setFilteredDocuments(filtered);
  }, [documents, searchTerm, selectedFilter]);

  const fetchFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/files/list");
      if (res.data.success) {
        setDocuments(res.data.files || []);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to fetch files");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    setUploading(true);
    setError(null);

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        
        const res = await api.post("/files/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        if (res.data.success) {
          setDocuments((prev) => [
            {
              id: res.data.file_id,
              filename: res.data.filename,
              file_type: res.data.file_type,
              file_size: res.data.file_size,
              upload_date: res.data.upload_date,
              status: "uploaded",
              ingest_status: res.data.ingest_status || (res.data.semantic_stored ? "done" : "pending"),
              chunk_count: res.data.chunk_count || 0,
              ingest_error: res.data.ingest_error || null,
            },
            ...prev,
          ]);
        }
      } catch (err) {
        setError(err.response?.data?.detail || `Failed to upload ${file.name}`);
      }
    }
    setUploading(false);
    event.target.value = "";
  };

  const handleDelete = async (fileId, filename) => {
    if (!window.confirm(`Delete "${filename}"?`)) return;

    try {
      const res = await api.delete(`/files/${fileId}`);
      if (res.data.success) {
        setDocuments((prev) => prev.filter((doc) => doc.id !== fileId));
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete file");
    }
  };

  const openChunkViewer = async (file) => {
    setSelectedChunkFile(file);
    setChunkViewerLoading(true);
    setChunkViewerError(null);
    setSemanticChunks([]);

    try {
      const res = await api.get(`/files/${file.id}`);
      const fileData = res.data?.file || {};
      const chunks = fileData?.extracted_fields?.chunks || [];

      if (!Array.isArray(chunks) || chunks.length === 0) {
        if (fileData.ingest_status === "failed") {
          setChunkViewerError(fileData.ingest_error || "Semantic chunking failed for this file.");
        } else if (fileData.ingest_error) {
          setChunkViewerError(fileData.ingest_error);
        }
      }

      setSemanticChunks(Array.isArray(chunks) ? chunks : []);
    } catch (err) {
      setChunkViewerError(err.response?.data?.detail || "Failed to load semantic chunks");
    } finally {
      setChunkViewerLoading(false);
    }
  };

  const closeChunkViewer = () => {
    setSelectedChunkFile(null);
    setChunkViewerError(null);
    setChunkViewerLoading(false);
    setSemanticChunks([]);
  };

  const formatEntityValue = (value) => {
    if (value == null) return "";
    if (Array.isArray(value)) return value.join(", ");
    if (typeof value === "object") {
      return Object.entries(value)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
        .join(" | ");
    }
    return String(value);
  };

  const totalDocs = documents.length;
  const totalSize = useMemo(
    () => documents.reduce((sum, doc) => sum + doc.file_size, 0),
    [documents]
  );

  const fileTypes = useMemo(() => {
    const types = {};
    documents.forEach((doc) => {
      types[doc.file_type] = (types[doc.file_type] || 0) + 1;
    });
    return types;
  }, [documents]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#f7fafb] to-[#ececec]">
      {/* Compact Header for Extension Interface */}
      <div className="sticky top-0 z-30 border-b border-[#d5dce1] bg-white shadow-sm">
        <div className="px-6 py-3 md:px-10 lg:px-14 flex items-center justify-between max-w-full">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#0f4d3d] to-[#06332a] flex items-center justify-center">
              <span className="text-white font-bold">A</span>
            </div>
            <span className="text-lg font-black text-[#0f4d3d]">AutoFill</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-[#153347]">{user?.name}</p>
              <p className="text-xs text-[#577181]">{user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-semibold rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6 py-8 md:px-10 lg:px-14">
        <section className="mx-auto max-w-7xl">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-[#0f4d3d] to-[#06332a] flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-[#55717f]">File Management</p>
              <h1 className="text-3xl md:text-4xl font-black text-[#0f4d3d]">Your Documents</h1>
            </div>
          </div>
          <p className="text-[#2c3f4f] max-w-2xl">
            Manage your uploaded documents. Upload new files, organize them, and prepare for autofill.
          </p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-3">
            <span className="text-lg mt-0.5">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-[#d5dce1] bg-white p-5 shadow-sm hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Total Files</p>
                <p className="mt-2 text-3xl font-black text-[#0f4d3d]">{totalDocs}</p>
              </div>
              <span className="text-3xl">📁</span>
            </div>
          </div>

          <div className="rounded-xl border border-[#d5dce1] bg-white p-5 shadow-sm hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Total Size</p>
                <p className="mt-2 text-3xl font-black text-[#0f4d3d]">{formatFileSize(totalSize)}</p>
              </div>
              <span className="text-3xl">💾</span>
            </div>
          </div>

          <div className="rounded-xl border border-[#d5dce1] bg-white p-5 shadow-sm hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">File Types</p>
                <p className="mt-2 text-3xl font-black text-[#0f4d3d]">{Object.keys(fileTypes).length || 0}</p>
              </div>
              <span className="text-3xl">🏷️</span>
            </div>
          </div>

          <div className="rounded-xl border border-[#d5dce1] bg-white p-5 shadow-sm hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Status</p>
                <p className="mt-2 text-3xl font-black text-[#0f7a4f]">✓ Ready</p>
              </div>
              <span className="text-3xl">🎯</span>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-[1.2fr_1.8fr]">
          {/* Upload Section */}
          <section className="rounded-2xl border border-[#c8d2d8] bg-gradient-to-br from-[#0f4d3d] to-[#06332a] p-6 text-white shadow-lg">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">📤</span>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-[#b8f2dd]">Upload</p>
                <h2 className="text-2xl font-black">Add Files</h2>
              </div>
            </div>
            <p className="text-[#c6f6e3] mb-6">Select multiple files or drag & drop them here</p>

            <label className="flex h-48 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#8be0bf] bg-[#145744] px-4 text-center transition hover:bg-[#1a6450] group">
              <span className="text-5xl mb-3 group-hover:scale-110 transition">{uploading ? "⏳" : "📥"}</span>
              <span className="text-lg font-semibold">{uploading ? "Uploading..." : "Drop files here"}</span>
              <span className="text-sm text-[#c6f6e3] mt-1">or click to browse</span>
              <input
                type="file"
                multiple
                disabled={uploading}
                onChange={handleUpload}
                className="hidden"
                accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.jpg,.png"
              />
            </label>

            <div className="mt-6 pt-6 border-t border-[#1a6450]">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#b8f2dd] mb-2">Supported</p>
              <p className="text-sm text-[#c6f6e3]">PDF • DOCX • XLSX • TXT • JPG • PNG</p>
            </div>
          </section>

          {/* Files Section */}
          <section className="rounded-2xl border border-[#c8d2d8] bg-white p-6 shadow-lg">
            {/* Header with Search */}
            <div className="mb-6">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div>
                  <h2 className="text-2xl font-black text-[#0f4d3d]">Documents</h2>
                  <p className="text-xs text-[#577181] mt-1">
                    {filteredDocuments.length} of {documents.length} files
                  </p>
                </div>
                <span className="rounded-full bg-[#edf6ff] px-3 py-1 text-sm font-semibold text-[#2561a6]">
                  {filteredDocuments.length} items
                </span>
              </div>

              {/* Search Bar */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="🔍 Search files..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="flex-1 rounded-lg border border-[#d5dce1] bg-[#f7fafb] px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0f4d3d] focus:border-transparent"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm("")}
                    className="px-3 py-2 text-sm text-[#577181] hover:text-[#2c3f4f] transition"
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Filter Chips */}
              <div className="mt-3 flex flex-wrap gap-2">
                {["all", "pdf", "docx", "xlsx"].map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedFilter(type)}
                    className={`px-3 py-1 text-xs font-semibold rounded-full transition ${
                      selectedFilter === type
                        ? "bg-[#0f4d3d] text-white"
                        : "border border-[#d5dce1] text-[#577181] hover:border-[#0f4d3d]"
                    }`}
                  >
                    {type === "all" ? "All Files" : type.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Files List */}
            {loading ? (
              <div className="py-12 text-center">
                <span className="text-4xl animate-bounce">⏳</span>
                <p className="mt-3 text-[#577181]">Loading your files...</p>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="py-12 text-center">
                <span className="text-5xl mb-3 block">📭</span>
                <p className="text-[#577181]">
                  {documents.length === 0
                    ? "No files yet. Start uploading!"
                    : "No files match your search"}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredDocuments.map((doc) => (
                  <article
                    key={doc.id}
                    className="rounded-lg border border-[#d6dde2] bg-[#fbfdff] p-4 transition hover:border-[#0f4d3d] hover:shadow-md group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-3xl pt-1">{getFileIcon(doc.file_type)}</div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-[#153347] truncate group-hover:text-[#0f4d3d]">
                            {doc.filename}
                          </p>
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-[#577181]">
                            <span className="font-medium">{doc.file_type}</span>
                            <span>•</span>
                            <span>{formatFileSize(doc.file_size)}</span>
                            <span>•</span>
                            <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                            <span>•</span>
                            <span className="font-semibold">Chunks: {doc.chunk_count || 0}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="rounded-full bg-[#daf5e9] px-2 py-1 text-xs font-bold text-[#0f7a4f]">
                          {doc.status}
                        </span>
                        <span
                          className={`rounded-full px-2 py-1 text-xs font-bold ${
                            doc.ingest_status === "done"
                              ? "bg-[#daf5e9] text-[#0f7a4f]"
                              : doc.ingest_status === "failed"
                                ? "bg-red-100 text-red-700"
                                : "bg-[#edf6ff] text-[#2561a6]"
                          }`}
                          title={doc.ingest_error || "Semantic chunking status"}
                        >
                          {doc.ingest_status || "pending"}
                        </span>
                        <button
                          type="button"
                          onClick={() => openChunkViewer(doc)}
                          className="rounded-lg border border-[#c8d2d8] bg-white px-2.5 py-1.5 text-xs font-semibold text-[#0f4d3d] transition hover:border-[#0f4d3d] hover:bg-[#f0fbf7]"
                          title="View semantic chunks"
                        >
                          🧠 Chunks
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="rounded-lg border border-red-200 px-2.5 py-1.5 text-xs font-semibold text-red-600 transition hover:border-red-400 hover:bg-red-50"
                          title="Delete file"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* File Type Summary */}
        {documents.length > 0 && (
          <div className="mt-8 rounded-xl border border-[#d5dce1] bg-white p-6 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#55717f] mb-4">
              File Type Summary
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
              {Object.entries(fileTypes).map(([type, count]) => (
                <div
                  key={type}
                  className="flex items-center justify-between rounded-lg bg-[#f7fafb] p-3 border border-[#e8eef3]"
                >
                  <span className="text-2xl">{getFileIcon(type)}</span>
                  <div className="text-right">
                    <p className="text-xs font-semibold text-[#55717f]">{type}</p>
                    <p className="text-lg font-black text-[#0f4d3d]">{count}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
      </div>

      {selectedChunkFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4">
          <div className="max-h-[85vh] w-full max-w-4xl overflow-hidden rounded-2xl border border-[#c8d2d8] bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#d6dde2] bg-gradient-to-r from-[#0f4d3d] to-[#06332a] px-5 py-4 text-white">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[#b8f2dd]">Semantic Viewer</p>
                <h3 className="text-lg font-black">{selectedChunkFile.filename}</h3>
              </div>
              <button
                type="button"
                onClick={closeChunkViewer}
                className="rounded-lg border border-white/30 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Close
              </button>
            </div>

            <div className="max-h-[70vh] overflow-y-auto p-5">
              {chunkViewerLoading ? (
                <div className="py-10 text-center text-[#577181]">
                  <p className="text-3xl">⏳</p>
                  <p className="mt-2">Loading semantic chunks...</p>
                </div>
              ) : chunkViewerError ? (
                <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {chunkViewerError}
                </div>
              ) : semanticChunks.length === 0 ? (
                <div className="rounded-lg border border-[#d6dde2] bg-[#f7fafb] px-4 py-5 text-sm text-[#577181]">
                  No semantic chunks found for this file yet. If upload just completed, wait a moment and reopen.
                </div>
              ) : (
                <div className="space-y-3">
                  {semanticChunks.map((chunk, index) => {
                    const entities = chunk.entities || {};
                    return (
                      <article
                        key={chunk.chunk_id ?? index}
                        className="rounded-xl border border-[#d6dde2] bg-[#fbfdff] p-4"
                      >
                        <div className="mb-3 flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-[#e6f4ee] px-2.5 py-1 text-xs font-bold text-[#0f7a4f]">
                            {chunk.category || "other"}
                          </span>
                          <span className="rounded-full bg-[#edf6ff] px-2.5 py-1 text-xs font-semibold text-[#2561a6]">
                            {chunk.sub_category || "general"}
                          </span>
                          <span className="rounded-full bg-[#f4f4f4] px-2.5 py-1 text-xs font-semibold text-[#334e62]">
                            Confidence: {typeof chunk.confidence === "number" ? chunk.confidence.toFixed(2) : "0.00"}
                          </span>
                          {chunk.needs_review && (
                            <span className="rounded-full bg-[#fff1d6] px-2.5 py-1 text-xs font-bold text-[#925d00]">
                              Needs Review
                            </span>
                          )}
                          <span className="text-xs font-semibold text-[#577181]">
                            Chunk #{chunk.chunk_id ?? index}
                          </span>
                        </div>

                        {Array.isArray(chunk.mapped_fields) && chunk.mapped_fields.length > 0 && (
                          <div className="mb-3 flex flex-wrap gap-1.5">
                            {chunk.mapped_fields.map((fieldName) => (
                              <span
                                key={fieldName}
                                className="rounded-full border border-[#d6dde2] bg-white px-2 py-1 text-[11px] font-semibold text-[#0f4d3d]"
                              >
                                {fieldName}
                              </span>
                            ))}
                          </div>
                        )}

                        {chunk.needs_review && chunk.review_reason && (
                          <div className="mb-3 rounded-lg border border-[#ffd7a3] bg-[#fff9ef] px-3 py-2 text-xs text-[#7c4a00]">
                            {chunk.review_reason}
                          </div>
                        )}

                        <p className="rounded-lg bg-white p-3 text-sm leading-relaxed text-[#153347] border border-[#e8eef3]">
                          {chunk.text || "No text"}
                        </p>

                        {Object.keys(entities).length > 0 && (
                          <div className="mt-3 grid gap-2 sm:grid-cols-2">
                            {Object.entries(entities).map(([key, value]) => {
                              const displayValue = formatEntityValue(value);
                              if (!displayValue) return null;
                              return (
                                <div key={key} className="rounded-lg border border-[#e8eef3] bg-white p-2.5">
                                  <p className="text-[10px] font-bold uppercase tracking-wider text-[#55717f]">
                                    {key.replaceAll("_", " ")}
                                  </p>
                                  <p className="mt-1 text-xs text-[#153347]">{displayValue}</p>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default Dashboard;
