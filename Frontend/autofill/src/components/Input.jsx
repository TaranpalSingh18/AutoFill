import React from "react";

const inputSomething = (e) =>{
    console.log("User is Typing")
}

const Input = ({ input, label, ...props }) => {
  return (
    <div className="flex flex-col gap-2 w-80">
      
      <label className="text-sm font-medium text-gray-700">
        {label}
      </label>

      <input
        type={input}
        {...props}
        className="px-4 py-2 border border-gray-300 rounded-xl 
                   focus:outline-none focus:ring-2 focus:ring-blue-500 
                   focus:border-blue-500 transition duration-200"
                   onChange={inputSomething}
      />

      



    </div>
  );
};

export default Input;