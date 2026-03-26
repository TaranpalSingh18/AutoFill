import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const Signup = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const routeHome = () => {
    navigate("/home");
  };

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(form);
  };

  return (
    <div className="min-h-screen bg-[#ececec] md:flex">
      <section className="w-full bg-[#ececec] px-8 py-8 md:w-[440px] md:shrink-0 md:px-10 md:py-12 lg:w-[500px] lg:px-12">
        <div className="mx-auto w-full max-w-[360px]">
          <button
            type="button"
            onClick={routeHome}
            className="mb-2 mt-2 inline-flex items-center gap-1 text-sm font-semibold text-[#145744] transition hover:text-[#0b3f31] hover:underline"
          >
            <span aria-hidden="true">←</span>
            Back to home
          </button>

          <p className="text-4xl font-semibold tracking-tight text-[#0d6149]">AutoFill.</p>

          <h1 className="mt-8 text-2xl font-bold leading-[1.05] text-[#0f4d3d] md:text-5xl">Create your AutoFill account</h1>

          <p className="mt-4 text-lg font-semibold leading-[1.25] text-[#102c3e]">
            Already have an account?{" "}
            <Link to="/" className="text-[#1472f4] hover:underline">
              Log In
            </Link>
          </p>

          <div className="mt-8 space-y-3">
            <button
              type="button"
              className="flex h-12 w-full items-center justify-center gap-2 rounded-lg border border-[#a7b0b6] bg-white text-base font-semibold text-[#4b5f70] shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50"
            >
              <span className="text-lg text-[#ea4335]">G</span>
              Google
            </button>

            <button
              type="button"
              className="flex h-12 w-full items-center justify-center gap-2 rounded-lg border border-[#a7b0b6] bg-white text-base font-semibold text-[#4b5f70] shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50"
            >
              <span className="text-lg">◉</span>
              GitHub
            </button>
          </div>

          <div className="my-5 flex items-center gap-2">
            <div className="h-px flex-1 bg-[#c0c7cd]" />
            <span className="text-base text-[#6f7f8b]">Or sign up with email</span>
            <div className="h-px flex-1 bg-[#c0c7cd]" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="mb-1 block text-[18px] font-semibold text-[#345063]">Full Name</label>
              <input
                type="text"
                name="name"
                placeholder="Enter your name"
                value={form.name}
                onChange={handleChange}
                className="h-12 w-full rounded-lg border border-[#9ca8af] bg-transparent px-3 text-lg text-[#2c3f4f] outline-none focus:border-[#2f92ff] focus:shadow-[0_0_0_2px_rgba(47,146,255,0.25)]"
              />
            </div>

            <div>
              <label className="mb-1 block text-[18px] font-semibold text-[#345063]">Email Address</label>
              <input
                type="email"
                name="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                className="h-12 w-full rounded-lg border border-[#9ca8af] bg-transparent px-3 text-lg text-[#2c3f4f] outline-none focus:border-[#2f92ff] focus:shadow-[0_0_0_2px_rgba(47,146,255,0.25)]"
              />
            </div>

            <div>
              <label className="mb-1 block text-[18px] font-semibold text-[#345063]">Password</label>
              <input
                type="password"
                name="password"
                placeholder="Create a strong password"
                value={form.password}
                onChange={handleChange}
                className="h-12 w-full rounded-lg border border-[#9ca8af] bg-transparent px-3 text-lg text-[#2c3f4f] outline-none focus:border-[#2f92ff] focus:shadow-[0_0_0_2px_rgba(47,146,255,0.25)]"
              />
            </div>

            <button
              type="submit"
              className="mt-5 h-12 w-full rounded-lg bg-[#0f4d3d] px-8 text-base font-semibold text-white shadow-sm transition hover:bg-[#0c3d31]"
            >
              Create Account
            </button>
          </form>
        </div>
      </section>

      <section className="relative hidden flex-1 overflow-hidden bg-[#056f53] p-14 text-white md:block">
        <div className="relative z-10 max-w-[560px]">
          <h2 className="text-[60px] font-extrabold leading-[1.03]">
            Fill Repetitive
            <br />
            Forms in
            <br />
            Seconds
          </h2>
          <p className="mt-7 max-w-[480px] text-lg leading-[1.35] text-[#e6fff6] lg:text-xl">
            Save user details once, reuse them anywhere, and auto-complete long forms with one click.
          </p>
          <button className="mt-9 border-b border-white pb-0.5 text-[34px] font-semibold">See how it works →</button>
        </div>

        <div className="absolute -right-16 -top-20 h-60 w-52 rotate-12 rounded-3xl border-4 border-black bg-[#1270e7]" />
        <div className="absolute right-16 top-8 h-72 w-36 rotate-12 rounded-2xl border-4 border-black bg-[#2bc3f1]" />

        <div className="absolute right-24 top-52 h-[480px] w-[480px] rotate-12 rounded-[70px] border-4 border-black bg-[#cbe988] shadow-[26px_26px_0_#000]" />
        <div className="absolute right-40 top-72 h-[160px] w-[160px] rounded-[26px] border-4 border-black bg-[#1f74ea]" />
        <div className="absolute right-60 top-[220px] h-9 w-9 rounded-full border-4 border-black bg-[#2ec8f4]" />
      </section>
    </div>
  );
};

export default Signup;