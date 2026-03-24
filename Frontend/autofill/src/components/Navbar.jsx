
const labels = ["Home", "About", "Features", "Contact Us"]
const args = ["Signup", "Login"]


const Navbar = () => {
    return (

        <nav className="bg-black text-white flex justify-between  p-4">
            
        <h1 className="font-bold">Logo</h1>

            <ul className="flex gap-10 mx-auto">
                {labels.map((item, index) =>(
                    <li key={index} className="cursor-pointer">
                        {item}
                    </li>
                ))}
            </ul>

            <ul className="flex gap-10">
                {args.map((item, index)=>(
                    <li key={index} className="cursor-pointer">
                        {item}
                    </li>
                ))}
            </ul>

            
        </nav>
    )
}

export default Navbar