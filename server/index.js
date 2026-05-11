const express = require("express");

const app = express();
const port = Number(process.env.PORT || 3000);

app.use(express.json());

app.use("/api/system", require("./routes/system"));
app.use("/api/direct", require("./routes/direct"));

app.get("/health", (req, res) => {
  res.json({ ok: true });
});

app.listen(port, () => {
  console.log(`Atlas Lab supervisor server listening on ${port}`);
});
