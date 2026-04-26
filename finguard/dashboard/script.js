let interval = null;
let isLive = false;

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Frontend ready");

    document.getElementById("simulateBtn")
        .addEventListener("click", triggerEvent);

    document.getElementById("liveBtn")
        .addEventListener("click", toggleLive);
});


// ==============================
// 🚀 API CALL
// ==============================
async function triggerEvent() {
    try {
        const res = await fetch("/webhook", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                eventType: "entityUpdated",
                entityType: "table",
                entity: { name: getRandomTable() },
                changeDescription: {
                    fieldsUpdated: [{ name: "columns" }]
                }
            })
        });

        const text = await res.text();

        let data;
        try {
            data = JSON.parse(text);
        } catch {
            console.error("❌ Invalid JSON:", text);
            return;
        }

        console.log("✅ Data:", data);

        updateUI(data);
        updateFeed(data);

    } catch (err) {
        console.error("❌ Request failed:", err);
    }
}


// ==============================
// 🔁 LIVE FEED
// ==============================
function toggleLive() {
    const btn = document.getElementById("liveBtn");

    if (isLive) {
        clearInterval(interval);
        isLive = false;
        btn.innerText = "Start Live Feed";
    } else {
        interval = setInterval(triggerEvent, 3000);
        isLive = true;
        btn.innerText = "Stop Live Feed";
    }
}


// ==============================
// 🎲 RANDOM TABLE
// ==============================
function getRandomTable() {
    const tables = [
        "raw_transactions",
        "processed_transactions",
        "payment_settlements",
        "fraud_scores"
    ];
    return tables[Math.floor(Math.random() * tables.length)];
}


// ==============================
// 🧠 NORMALIZE DATA
// ==============================
function normalize(data) {
    return {
        table: data?.table || "unknown",
        risk: data?.risk || "UNKNOWN",
        financial: data?.financial_risk || "N/A",
        downstream: data?.downstream_tables || [],
        ai: data?.ai_insight || {}
    };
}


// ==============================
// 🧠 UPDATE UI
// ==============================
function updateUI(raw) {
    if (!raw || raw.status !== "processed") return;

    const d = normalize(raw);

    set("tableName", d.table);
    set("financialRisk", d.financial);
    set("businessImpact", d.ai.business_impact || "N/A");
    set("reasoning", d.ai.reasoning || "N/A");
    set("confidence", d.ai.confidence ?? "N/A");
    set("recommendedAction", d.ai.recommended_action || "N/A");

    // lineage
    set(
        "lineage",
        d.downstream.length
            ? `${d.table} → ${d.downstream.join(", ")}`
            : "No lineage"
    );

    updateRiskBadge(d.risk);
}


// ==============================
// 📡 FEED
// ==============================
function updateFeed(raw) {
    const d = normalize(raw);

    const feed = document.getElementById("feed");

    const item = document.createElement("div");
    item.className =
        "bg-slate-700 p-3 rounded flex justify-between";

    item.innerHTML = `
        <div>
            <div class="font-bold">${d.table}</div>
            <div class="text-sm">${d.financial}</div>
        </div>
        <div style="color:${color(d.risk)}; font-weight:bold">
            ${d.risk}
        </div>
    `;

    feed.prepend(item);

    if (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }
}


// ==============================
// 🧱 SAFE SET
// ==============================
function set(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value;
}


// ==============================
// 🎨 BADGE
// ==============================
function updateRiskBadge(risk) {
    const el = document.getElementById("riskBadge");
    if (!el) return;

    el.innerText = risk;
    el.className = "px-3 py-1 rounded font-bold";

    if (risk === "HIGH") el.classList.add("bg-red-500");
    else if (risk === "MEDIUM") el.classList.add("bg-yellow-500");
    else el.classList.add("bg-green-500");
}

function color(risk) {
    if (risk === "HIGH") return "#ef4444";
    if (risk === "MEDIUM") return "#f59e0b";
    return "#10b981";
}