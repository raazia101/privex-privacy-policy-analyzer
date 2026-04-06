async function loadGraph() {
    const urlParams = new URLSearchParams(window.location.search);
    const pageUrl = urlParams.get("url");

    console.log("Fetching graph for:", pageUrl);

    try {
        const response = await fetch("http://127.0.0.1:5000/graph", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: pageUrl })
        });

        const result = await response.json();
        console.log("Graph API Result:", result);

        if (!result.nodes || result.nodes.length === 0) {
            document.getElementById("network").innerHTML = "No graph data available.";
            return;
        }

        const nodes = new vis.DataSet(result.nodes);
        const edges = new vis.DataSet(result.edges);

        const container = document.getElementById("network");
        const data = { nodes: nodes, edges: edges };

        const options = {
            nodes: {
                shape: "ellipse",
                size: 20,
                font: { size: 14 }
            },
            edges: {
                arrows: "to",
                smooth: true,
                font: { align: "middle" }
            },
            physics: {
                enabled: true,
                stabilization: true
            }
        };

        new vis.Network(container, data, options);

    } catch (error) {
        console.error("Graph Load Error:", error);
        document.getElementById("network").innerHTML = "Error loading graph.";
    }
}

loadGraph();
