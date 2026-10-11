# 🔬 AbiLens — ABI & Event Decoder (MIT)

Paste a contract address or tx hash → human-readable JSON for Input Data
and Event Logs. UI in EN/TR/AR. Static single file + README.

## How it works (no dependencies)

- **Signature DBs:** OpenChain (filtered) → 4byte fallback resolve
  selectors/topics to `name(types)` text.
- **Built-in ABI decoder:** address, uint/int (signed, arbitrary width),
  bool, bytes<M>, string, bytes, arrays (static + dynamic), tuples.
  Byte-exact offsets with sanity caps (no tab hangs on malformed hex).
- **On-chain fetch:** public RPC presets (Ethereum/BSC/Polygon/Arbitrum/Base)
  via `eth_getTransactionByHash` + `eth_getTransactionReceipt`.
- **ABI paste:** exact param names/types when provided; DB text otherwise;
  raw words fallback when unknown. Markdown/JSON download.

## Money & contact

- `CONFIG.ads`: CoinZilla (`coinzillaSrc`+`coinzillaZone`), Cointraffic,
  or AdSense fallback.
- Donate: BTC + USDT-TRC20 live. **EVM + Solana slots reserved —
  add addresses to `CONFIG.pay`.**
- 📧 baranavisat@gmail.com · 📞 +90 531 326 37 22 · WhatsApp

## Run

```bash
cd abilens
python3 -m http.server 8080
```

## License

MIT. Verify critical data on a block explorer.
