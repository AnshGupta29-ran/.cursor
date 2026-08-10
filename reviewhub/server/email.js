// Email behind a provider interface: routes never await SMTP, so a slow or
// down mail server can't stall the request path. Console provider by default;
// SMTP/SES implements the same one-method contract in production.
const provider = {
  send(to, subject, body) {
    console.log(`[email stub] to=${to} subject="${subject}" body="${body}"`);
    return Promise.resolve();
  }
};

export function sendEmail(to, subject, body) {
  provider.send(to, subject, body).catch(err => console.error('[email] failed:', err.message));
}
