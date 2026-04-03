import { useState, useRef, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/authService";

const UserMenu = () => {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [recentFiles, setRecentFiles] = useState([]);
  const [showProfile, setShowProfile] = useState(false);
  const menuRef = useRef(null);

  // Fetch recent files
  useEffect(() => {
    if (isOpen) {
      fetchRecentFiles();
    }
  }, [isOpen]);

  const fetchRecentFiles = async () => {
    try {
      const res = await api.get("/files/list");
      if (res.data.success) {
        setRecentFiles(res.data.files?.slice(0, 3) || []);
      }
    } catch (err) {
      console.error("Failed to fetch recent files:", err);
    }
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  return (
    <>
      <div className="relative" ref={menuRef}>
        {/* User Avatar Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-3 rounded-lg bg-[#f0f0f0] px-3 py-2 transition hover:bg-[#e5e5e5]"
        >
          <span className="h-8 w-8 rounded-full bg-gradient-to-br from-[#0f4d3d] to-[#06332a] text-white flex items-center justify-center text-xs font-bold shadow-sm">
            {user.name?.[0]?.toUpperCase() || "U"}
          </span>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold text-[#2c3f4f]">{user.name}</p>
            <p className="text-xs text-[#577181]">{user.email}</p>
          </div>
          <svg
            className={`h-4 w-4 text-[#577181] transition ${
              isOpen ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute right-0 top-12 z-50 w-72 rounded-xl border border-[#d5dce1] bg-white shadow-lg">
            {/* User Info Section */}
            <div className="border-b border-[#e8eef3] px-4 py-4">
              <div className="flex items-center gap-3">
                <span className="h-12 w-12 rounded-full bg-gradient-to-br from-[#0f4d3d] to-[#06332a] text-white flex items-center justify-center text-sm font-bold shadow">
                  {user.name?.[0]?.toUpperCase()}
                </span>
                <div>
                  <p className="font-semibold text-[#153347]">{user.name}</p>
                  <p className="text-sm text-[#577181]">{user.email}</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="py-2">
              <button
                onClick={() => {
                  setShowProfile(true);
                  setIsOpen(false);
                }}
                className="w-full px-4 py-2 text-left text-sm text-[#2c3f4f] hover:bg-[#f7fafb] transition flex items-center gap-3"
              >
                <svg className="h-4 w-4 text-[#0f4d3d]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                View Profile
              </button>

              <a
                href="mailto:support@autofill.com"
                className="w-full px-4 py-2 text-left text-sm text-[#2c3f4f] hover:bg-[#f7fafb] transition flex items-center gap-3 block"
              >
                <svg className="h-4 w-4 text-[#0f4d3d]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.5 1.5H3.75A2.25 2.25 0 001.5 3.75v16.5A2.25 2.25 0 003.75 22.5h16.5a2.25 2.25 0 002.25-2.25V13.5m-18-12h13.5m-13.5 9h9" />
                </svg>
                Help & Support
              </a>
            </div>

            {/* Recent Files */}
            {recentFiles.length > 0 && (
              <>
                <div className="border-t border-[#e8eef3] px-4 py-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f] mb-2">Recent Files</p>
                  {recentFiles.map((file) => (
                    <div
                      key={file.id}
                      className="py-2 px-2 rounded hover:bg-[#f7fafb] transition cursor-pointer"
                    >
                      <p className="text-sm font-medium text-[#153347] truncate">{file.filename}</p>
                      <p className="text-xs text-[#577181]">
                        {file.file_type} • {file.file_size > 1024000 ? `${(file.file_size / 1024000).toFixed(1)} MB` : `${(file.file_size / 1024).toFixed(1)} KB`}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Logout Button */}
            <div className="border-t border-[#e8eef3] px-4 py-2">
              <button
                onClick={() => {
                  logout();
                  setIsOpen(false);
                }}
                className="w-full rounded-lg border border-red-200 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 transition"
              >
                Logout
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Profile Modal */}
      {showProfile && (
        <ProfileModal
          user={user}
          onClose={() => setShowProfile(false)}
        />
      )}
    </>
  );
};

// Profile Modal Component
const ProfileModal = ({ user, onClose }) => {
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 border border-[#d5dce1]">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#577181] hover:text-[#2c3f4f]"
        >
          ✕
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#0f4d3d] to-[#06332a] text-white flex items-center justify-center text-2xl font-bold mx-auto shadow-md mb-4">
            {user.name?.[0]?.toUpperCase()}
          </div>
          <h2 className="text-2xl font-bold text-[#0f4d3d]">{user.name}</h2>
          <p className="text-[#577181] mt-1">{user.email}</p>
        </div>

        {/* Info Cards */}
        <div className="space-y-3">
          <div className="rounded-lg border border-[#e8eef3] bg-[#f7fafb] p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Member Since</p>
            <p className="text-sm font-medium text-[#153347] mt-1">{formatDate(user.created_at)}</p>
          </div>

          <div className="rounded-lg border border-[#e8eef3] bg-[#f7fafb] p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Account Status</p>
            <p className="text-sm font-medium text-[#0f7a4f] mt-1">✓ Active</p>
          </div>

          <div className="rounded-lg border border-[#e8eef3] bg-[#f7fafb] p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f]">Email Verified</p>
            <p className="text-sm font-medium text-[#0f7a4f] mt-1">✓ Yes</p>
          </div>
        </div>

        {/* Settings Section */}
        <div className="mt-6 border-t border-[#e8eef3] pt-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#55717f] mb-3">Preferences</p>
          
          <div className="space-y-2">
            <label className="flex items-center gap-3 cursor-pointer hover:bg-[#f7fafb] p-2 rounded">
              <input type="checkbox" className="w-4 h-4" defaultChecked />
              <span className="text-sm text-[#2c3f4f]">Email notifications</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer hover:bg-[#f7fafb] p-2 rounded">
              <input type="checkbox" className="w-4 h-4" defaultChecked />
              <span className="text-sm text-[#2c3f4f]">File upload alerts</span>
            </label>
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="w-full mt-6 rounded-lg bg-[#0f4d3d] px-4 py-2 text-white font-semibold hover:bg-[#0c3d31] transition"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default UserMenu;
