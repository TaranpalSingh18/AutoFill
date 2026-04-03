
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import UserMenu from "./UserMenu";

const Navbar = () => {
  const { user } = useAuth();

  return (
    <nav className="sticky top-0 z-40 flex flex-col border-b border-[#d5dce1] bg-white shadow-sm">
      {/* Main Navbar */}
      <div className="flex items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#0f4d3d] to-[#06332a] flex items-center justify-center">
            <span className="text-white font-bold text-lg">A</span>
          </div>
          <h1 className="text-2xl font-black text-[#0f4d3d] group-hover:text-[#06332a] transition">
            AutoFill
          </h1>
        </Link>

        {/* Navigation Links */}
        <div className="absolute left-1/2 -translate-x-1/2">
          <ul className="flex gap-8 text-sm font-semibold">
            <li>
              <Link
                to="/"
                className="text-[#2c3f4f] transition hover:text-[#0f4d3d] relative group"
              >
                Home
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#0f4d3d] transition-all group-hover:w-full"></span>
              </Link>
            </li>
            {user && (
              <li>
                <Link
                  to="/dashboard"
                  className="text-[#2c3f4f] transition hover:text-[#0f4d3d] relative group"
                >
                  Dashboard
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#0f4d3d] transition-all group-hover:w-full"></span>
                </Link>
              </li>
            )}
            <li>
              <Link
                to="/feature"
                className="text-[#2c3f4f] transition hover:text-[#0f4d3d] relative group"
              >
                Features
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#0f4d3d] transition-all group-hover:w-full"></span>
              </Link>
            </li>
            <li>
              <Link
                to="/about"
                className="text-[#2c3f4f] transition hover:text-[#0f4d3d] relative group"
              >
                About
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-[#0f4d3d] transition-all group-hover:w-full"></span>
              </Link>
            </li>
          </ul>
        </div>

        {/* Auth Section */}
        <div className="flex items-center gap-4">
          {user ? (
            <UserMenu />
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-semibold text-[#0f4d3d] hover:text-[#06332a] transition"
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-[#0f4d3d] text-white hover:bg-[#0c3d31] transition shadow-sm"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Optional: Breadcrumb for Dashboard */}
      {user && (
        <div className="hidden md:flex items-center gap-2 px-6 py-2 bg-[#f7fafb] border-t border-[#e8eef3] text-xs text-[#577181]">
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12a9 9 0 019-9 9.75 9.75 0 016.74 2.74L21 8" />
          </svg>
          <span>Welcome back, {user.name}!</span>
        </div>
      )}
    </nav>
  );
};

export default Navbar;