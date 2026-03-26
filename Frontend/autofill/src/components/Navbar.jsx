

import { Link } from "react-router-dom"


const Navbar = () => {
    return (

        <nav className="bg-black text-white flex justify-between  p-4">
            
        <h1 className="font-bold">Logo</h1>

            <ul className="flex gap-10 mx-auto cursor-pointer">
                <li><Link to="/">Home</Link></li>
                <li><Link to="/feature">Features</Link></li>
                <li><Link to="/about">About</Link></li>
            </ul>

            <ul className="flex gap-10 cursor-pointer mr-10">
                <li><Link to="/signup">Signup</Link></li>
                <li><Link to="/login">Login</Link></li>
            </ul>

            
        </nav>
    )
}

export default Navbar