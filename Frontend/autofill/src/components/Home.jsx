import React from "react";
import { Link } from "react-router-dom";
import Hero from "./Hero";

const Home = () => {
    return (
        <main className="w-full">
            <Hero />

            <section className="flex min-h-screen items-center justify-center bg-[#ececec] px-6 py-12">
                <div className="mx-auto max-w-5xl text-center">
                    <p className="text-sm font-semibold uppercase tracking-[0.14em] text-[#345063]">Why AutoFill</p>
                    <h2 className="mt-4 text-4xl font-black uppercase leading-[1.02] text-[#0f4d3d] sm:text-6xl" style={{ fontFamily: "'Host Grotesk', sans-serif" }}>
                        Forms should finish before your coffee cools.
                    </h2>
                    <p className="mx-auto mt-5 max-w-3xl text-lg font-semibold text-[#2c3f4f]">
                        AutoFill remembers your details and injects them instantly so every signup, checkout, and profile form takes seconds.
                    </p>
                </div>
            </section>

            <section className="flex min-h-screen items-center justify-center bg-[#0a3f33] px-6 py-12 text-white">
                <div className="mx-auto max-w-5xl text-center">
                    <p className="text-sm font-semibold uppercase tracking-[0.14em] text-[#b8f2dd]">Ready to start</p>
                    <h2 className="mt-4 text-4xl font-black uppercase leading-[1.02] text-[#e9fff7] sm:text-6xl" style={{ fontFamily: "'Host Grotesk', sans-serif" }}>
                        Stop typing. Start finishing.
                    </h2>
                    <div className="mt-8 flex items-center justify-center gap-3">
                        <Link
                            to="/signup"
                            className="rounded-lg bg-[#e9fff7] px-6 py-3 text-sm font-bold uppercase tracking-wide text-[#0f4d3d] transition hover:bg-white"
                        >
                            Create Account
                        </Link>
                    </div>
                </div>
            </section>
        </main>
    );
};

export default Home;