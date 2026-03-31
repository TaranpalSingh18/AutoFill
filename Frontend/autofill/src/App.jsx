import React from "react";
import Navbar from "./components/Navbar";
import { Route, Routes, useLocation} from "react-router-dom";
import Signup from "./components/Signup";
import Home from "./components/Home";

// const labels = [
//   {
//           image_url:"https://plus.unsplash.com/premium_photo-1670787505459-5ec84cc48762?q=80&w=686",
//           name:"Emma Watson",
//           age:30,
//           race:"Asian"
//   }, 
//   {
//           image_url:"https://images.unsplash.com/photo-1774247993490-7d1469a3de97?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
//           name:"Shane Warn",
//           age:30,
//           race:"African"
//   }, 
//     {
//           image_url:"https://plus.unsplash.com/premium_photo-1670787505459-5ec84cc48762?q=80&w=686",
//           name:"Emma Watson",
//           age:30,
//           race:"Asian"
//   }
// ]

const App = () => {
  const location = useLocation()
  const hideNavbar = location.pathname==="/signup"
  return (
    <div>
      {!hideNavbar && <Navbar/>}
        <Routes>
          <Route path="/" element={<Home/>}/>
          <Route path="/home" element={<Home/>}/>
          <Route path="/signup" element={<Signup/>} />
        </Routes>
    </div>
  );
};

export default App;