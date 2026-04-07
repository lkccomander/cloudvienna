import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./app/router";
import { AuthProvider } from "./app/providers/AuthProvider";
import { I18nProvider } from "./app/providers/I18nProvider";
import { ThemeProvider } from "./app/providers/ThemeProvider";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <I18nProvider>
      <ThemeProvider>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ThemeProvider>
    </I18nProvider>
  </React.StrictMode>,
);
