import React, { useState } from "react";
import './App.css';


const App = () => {
    const [requirement, setRequirement] = useState("");
    const [diagramUrl, setDiagramUrl] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async () => {
        if (!requirement.trim()) {
            setError("Please enter a software requirement.");
            setShowModal(true);
            return;
        }

        setLoading(true);
        setError(null);
        setShowModal(false);

        try {
            const response = await fetch("http://localhost:8000/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ requirement })
            });

            if (!response.ok) throw new Error("Server error");

            const data = await response.json();
            setDiagramUrl(`http://localhost:8000${data.diagram_url}`);
            setShowModal(true);
        } catch (err) {
            setError("Failed to generate UML diagram.");
            setShowModal(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            {/* {loading && <div style={styles.loaderOverlay}><div style={styles.loader}></div></div>} */}
            {loading && (
                <div style={styles.loaderOverlay}>
                    <div className="loader"></div> {/* ← uses className, not inline style */}
                </div>
            )}

            <h2 style={styles.heading}>UML Diagram Generator</h2>

            <label style={styles.label}>Software Requirement:</label>
            <textarea
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                placeholder="e.g. A garage management system"
                style={styles.textarea}
            />

            <button style={styles.submitButton} onClick={handleSubmit} disabled={loading}>
                {loading ? "Generating..." : "Generate Diagram"}
            </button>

            {showModal && (
                <div style={styles.modalOverlay}>
                    <div style={styles.modal}>
                        <h3>{error ? "Error" : "Generated UML Diagram"}</h3>
                        {error ? (
                            <p>{error}</p>
                        ) : (
                            <img
                                src={diagramUrl}
                                alt="UML Diagram"
                                style={{ maxWidth: "100%", maxHeight: "500px", border: "1px solid #ccc" }}
                            />
                        )}
                        <button style={styles.closeButton} onClick={() => setShowModal(false)}>Close</button>
                    </div>
                </div>
            )}
        </div>
    );
};

const styles = {
    container: {
        padding: "20px",
        maxWidth: "600px",
        margin: "auto",
        backgroundColor: "#f0f4f8",
        borderRadius: "10px",
        boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
    },
    heading: {
        textAlign: "center",
        color: "#1a237e",
    },
    label: {
        display: "block",
        marginTop: "10px",
        fontWeight: "bold",
    },
    textarea: {
        width: "100%",
        height: "100px",
        padding: "10px",
        borderRadius: "5px",
        marginTop: "5px",
        border: "1px solid #ccc",
        fontSize: "14px"
    },
    submitButton: {
        backgroundColor: "#1a237e",
        color: "white",
        padding: "12px",
        border: "none",
        borderRadius: "5px",
        cursor: "pointer",
        fontSize: "16px",
        width: "100%",
        marginTop: "10px",
    },
    loaderOverlay: {
        position: "fixed", top: 0, left: 0, width: "100%", height: "100%",
        backgroundColor: "rgba(0, 0, 0, 0.6)", display: "flex",
        alignItems: "center", justifyContent: "center", zIndex: 10
    },
    loader: {
        width: "50px", height: "50px", borderRadius: "50%",
        border: "5px solid #fff", borderTopColor: "transparent",
        animation: "spin 1s linear infinite"
    },
    modalOverlay: {
        position: "fixed", top: 0, left: 0, width: "100%", height: "100%",
        backgroundColor: "rgba(0,0,0,0.5)", display: "flex",
        justifyContent: "center", alignItems: "center", zIndex: 20
    },
    modal: {
        background: "#fff", padding: "20px", borderRadius: "10px",
        boxShadow: "0 4px 8px rgba(0,0,0,0.2)", width: "90%",
        maxWidth: "800px", maxHeight: "90vh", overflowY: "auto", textAlign: "center"
    },
    closeButton: {
        marginTop: "15px",
        backgroundColor: "#d32f2f",
        color: "white",
        padding: "10px 20px",
        border: "none",
        borderRadius: "5px",
        cursor: "pointer"
    },
};

export default App;
