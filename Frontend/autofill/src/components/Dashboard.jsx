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
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="rounded-full bg-[#daf5e9] px-2 py-1 text-xs font-bold text-[#0f7a4f]">
                          {doc.status}
                        </span>
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
    </main>
  );
};

export default Dashboard;
