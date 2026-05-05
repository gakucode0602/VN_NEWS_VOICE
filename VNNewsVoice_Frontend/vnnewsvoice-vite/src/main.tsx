import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/index.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import App from "./app/App";
import AppProviders from "./app/providers";

ReactDOM.createRoot(document.getElementById("root")).render(
  <AppProviders>
    <App />
  </AppProviders>
);