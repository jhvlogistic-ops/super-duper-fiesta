const express = require("express");

const direct = require("../modules/direct-intervention-controller");

const router = express.Router();

router.post("/review", (req, res) => {
  const out = direct.reviewDirectOrder(req.body || {});
  res.json(out);
});

module.exports = router;
