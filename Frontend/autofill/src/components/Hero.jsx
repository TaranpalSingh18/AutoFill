import React from "react";
import { Link } from "react-router-dom";

const Hero = () => {
	return (
		<section className="relative isolate flex min-h-screen items-center overflow-hidden bg-[#0a3f33] px-4 py-16 text-white sm:px-8 md:px-10 md:py-24">
			<div className="pointer-events-none absolute inset-0 opacity-30">
				<div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(95,210,173,0.35),transparent_35%),radial-gradient(circle_at_80%_85%,rgba(47,146,255,0.18),transparent_40%)]" />
				<div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.08)_1px,transparent_1px)] bg-[size:52px_52px]" />
			</div>

			<p className="pointer-events-none absolute left-1/2 top-1/2 w-max -translate-x-1/2 -translate-y-1/2 select-none font-black uppercase leading-none tracking-tight text-white/12">
				{/* <span className="text-[20vw] opacity-0.1">Autofill Is Future</span> */}
			</p>

			<div className="relative z-10 mx-auto flex max-w-6xl flex-col items-center gap-10 lg:flex-row lg:items-stretch lg:justify-between">
				<div className="max-w-2xl text-center flex flex-col items-center">
					<p className="inline-flex rounded-full border border-[#8be0bf]/40 bg-[#114b3d] px-4 py-1 text-sm font-semibold text-[#b8f2dd] cursor-pointer">
						Autofill Smarter
					</p>

					<p className="mt-4 text-xl sm:text-2xl font-bold leading-tight text-[#b8f2dd] sm:text-2xl mb-1" style={{ fontFamily: "'Host Grotesk', sans-serif", letterSpacing: "0.01em" }}>
						store once. reuse everywhere cause
					</p>

                <h1 className="uppercase leading-none text-[#e9fff7] flex items-center justify-center gap-1" style={{ fontFamily: "'Host Grotesk', sans-serif", fontWeight: 900, WebkitTextStroke: "0.8px #e9fff7", letterSpacing: "0.02em" }}>
                    <span className="text-[8vw]">Typing</span>
                    <div className="flex items-center justify-center bg-[#e9fff7]  rounded-md border-2 border-white/20 -rotate-12 transform mt-3">
                        <span className="text-[6vw] sm:text-[5vw] md:text-[4vw] text-[#0a3f33] leading-none lowercase" style={{ fontFamily: "'Host Grotesk', sans-serif", fontWeight: 900, WebkitTextStroke: "0.5px #0a3f33", letterSpacing: "0.02em" }}>is</span>
                    </div>
                    <span className="text-[8vw]">Dead</span>
                </h1>

					<div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
						<Link
							to="/signup"
							className="rounded-lg bg-[#0f4d3d] px-6 py-3 text-sm font-bold uppercase tracking-wide text-white transition hover:-translate-y-0.5 hover:bg-[#0c3d31]"
						>
							Start Free
						</Link>
						<button
							type="button"
							className="rounded-lg border border-[#9bdcc3] bg-transparent px-6 py-3 text-sm font-bold uppercase tracking-wide text-[#d9fff1] transition hover:border-[#bff2de] hover:bg-white/10"
						>
							Watch Demo
						</button>
					</div>
				</div>

				{/* <div className="relative mx-auto w-full max-w-[340px] shrink-0 sm:max-w-[390px]">
					<div className="relative overflow-hidden rounded-[26px] border-2 border-black/60 bg-[#1472f4] p-6 shadow-[12px_12px_0_rgba(0,0,0,0.45)]">
						<div className="absolute -left-6 top-0 h-3 w-[calc(100%+48px)] bg-[radial-gradient(circle,rgba(0,0,0,0.6)_3px,transparent_3px)] bg-[length:14px_14px]" />
						<div className="absolute -left-6 bottom-0 h-3 w-[calc(100%+48px)] bg-[radial-gradient(circle,rgba(0,0,0,0.6)_3px,transparent_3px)] bg-[length:14px_14px]" />

						<div className="flex min-h-[260px] flex-col items-center justify-center rounded-[18px] border border-white/20 bg-[#2f92ff]/40">
							<span className="text-6xl font-black text-[#0b3f7a]">1</span>
							<span className="mt-16 text-sm font-bold uppercase tracking-wider text-white/90">Scratch to reveal</span>
						</div>
					</div>
				</div> */}
			</div>
		</section>
	);
};

export default Hero;

