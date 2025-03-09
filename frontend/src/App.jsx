import { useEffect, useState } from "react";
import { fetchHelloWorld } from "./api";
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
      fetchHelloWorld().then(setMessage);
  }, []);

  return (
      <div>
          <h1>React + Django</h1>
          <p>{message ? message : "Loading..."}</p>
      </div>
  );
}

export default App;
