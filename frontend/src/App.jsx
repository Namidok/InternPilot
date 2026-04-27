import { Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import InternshipDetailsPage from "./pages/InternshipDetailsPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/internships/:id" element={<InternshipDetailsPage />} />
    </Routes>
  );
}

export default App;