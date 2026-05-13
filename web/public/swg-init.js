/* Subscribe with Google (basic) initialiser.
 *
 * Registers HORIZON as a Google News Publisher Center product. The product
 * id `CAow_6PgCw:openaccess` is assigned by Publisher Center; the
 * `:openaccess` suffix declares this is a free / no-paywall publication
 * so Google News can surface our articles without subscriber gating.
 *
 * Loaded via <script src="/swg-init.js"> to keep `script-src 'self'`
 * CSP clean (no inline-script allowance needed).
 */
(self.SWG_BASIC = self.SWG_BASIC || []).push(function (basicSubscriptions) {
  basicSubscriptions.init({
    type: "NewsArticle",
    isPartOfType: ["Product"],
    isPartOfProductId: "CAow_6PgCw:openaccess",
    clientOptions: { theme: "light", lang: "en" },
  });
});
