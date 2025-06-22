document.getElementById("genereazaBtn").addEventListener("click", async () => {
  const textarea = document.getElementById("editarePostare");
  const stil = document.getElementById("stilSelect").value;
  textarea.value = "🔍 Preiau date din pagina activă...";

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const titlu = document.querySelector("h1, h2, .product-title")?.innerText || "Titlu necunoscut";
      const pret = [...document.querySelectorAll("*")].map(el => el.innerText)
        .find(t => t.match(/(\d+[\.,]?\d*)\s?(lei|RON|€|\$)/i)) || "Preț indisponibil";
      const descriere = document.querySelector("p, .description, .product-description")?.innerText || "Fără descriere";
      return { titlu, pret, descriere };
    }
  }, async (results) => {
    const produs = results?.[0]?.result;
    if (!produs) {
      textarea.value = "❌ Nu s-a putut extrage produsul.";
      return;
    }

    let prompt = "";
    if (stil === "funny") {
      prompt = `Scrie o postare de social media într-un stil amuzant și sarcastic, ca și cum un copywriter cool din internet face glume despre acest produs. Folosește jocuri de cuvinte, meme-style sau comparații absurde. Poți adăuga emoji, dar nu exagera.

Produs:
Titlu: ${produs.titlu}
Preț: ${produs.pret}
Descriere: ${produs.descriere}

Postarea trebuie să fie scurtă, memorabilă și super catchy.`;
    } else if (stil === "professional") {
      prompt = `Creează o postare profesională pentru social media, care pune în valoare avantajele competitive ale produsului. Include un slogan convingător și un apel la acțiune elegant. Tonul trebuie să inspire încredere, calitate și expertiză. Nu folosi glume.

Produs:
Titlu: ${produs.titlu}
Preț: ${produs.pret}
Descriere: ${produs.descriere}`;
    } else if (stil === "informative") {
      prompt = `Redactează o postare informativă și bine argumentată pentru social media. Include beneficiile cheie, tipul utilizatorului potrivit și un scor estimativ de rating de pe piață. Adaugă detalii utile și practice.

Produs:
Titlu: ${produs.titlu}
Preț: ${produs.pret}
Descriere: ${produs.descriere}`;
    }

    textarea.value = "🧠 Generez postarea...";

    try {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": "Bearer Cheia-api",  // înlocuiește cu cheia ta
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: "gpt-3.5-turbo",
          messages: [{ role: "user", content: prompt }]
        })
      });

      const data = await response.json();
      textarea.value = data.choices?.[0]?.message?.content || "⚠️ AI-ul nu a generat conținut.";
    } catch (err) {
      console.error("❌ Eroare API:", err);
      textarea.value = "❌ Eroare la generare. Verifică cheia sau conexiunea.";
    }
  });
});

document.getElementById("salveazaBtn").addEventListener("click", () => {
  const text = document.getElementById("editarePostare").value;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "postare-ai.txt";
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById("copiazaBtn").addEventListener("click", () => {
  const text = document.getElementById("editarePostare").value;
  navigator.clipboard.writeText(text).then(() => {
    alert("📋 Textul a fost copiat!");
  });
});
