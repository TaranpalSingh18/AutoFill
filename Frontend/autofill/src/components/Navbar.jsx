

import { Link } from "react-router-dom"


const Navbar = () => {
    return (

        <nav className="flex items-center justify-between border-b border-[#c0c7cd] bg-[#ececec] px-6 py-4 text-[#102c3e]">
            
        <h1 className="text-xl font-bold text-[#0f4d3d]">AutoFill.</h1>

            <ul className="mx-auto flex gap-10 text-[17px] font-semibold">
                <li><Link to="/" className="transition hover:text-[#0f4d3d]">Home</Link></li>
                <li><Link to="/feature" className="transition hover:text-[#0f4d3d]">Features</Link></li>
                <li><Link to="/about" className="transition hover:text-[#0f4d3d]">About</Link></li>
            </ul>

            <ul className="mr-2 flex items-center gap-4 text-sm font-semibold">
                <li>
                    <Link
                        to="/signup"
                        className="rounded-lg bg-[#0f4d3d] px-4 py-2 text-white transition hover:bg-[#0c3d31]"
                    >
                        Signup
                    </Link>
                </li>
                <li>
                    <Link
                        to="/login"
                        className="rounded-lg border border-[#9ca8af] px-4 py-2 text-[#345063] transition hover:border-[#0f4d3d] hover:text-[#0f4d3d]"
                    >
                        Login
                    </Link>
                </li>
            </ul>

            
        </nav>
    )
} 

export default Navbar