/**
 * Builds a UPI payment intent link (the `upi://pay` deep link most Indian
 * UPI apps -- GPay, PhonePe, Paytm, etc. -- register as a handler for).
 * Opening it hands off to the user's own UPI app with the amount and payee
 * pre-filled; the admin still has to approve/send from there themselves --
 * this is not an automated payout, just a shortcut to avoid re-typing.
 */
export function buildUpiPayLink({
  payeeIdentifier,
  payeeName,
  amount,
  note,
}: {
  /** A UPI VPA (e.g. "name@bank") or a plain phone number as a best-effort fallback. */
  payeeIdentifier: string
  payeeName: string
  amount?: string
  note?: string
}): string {
  const params = new URLSearchParams({
    pa: payeeIdentifier,
    pn: payeeName,
    cu: 'INR',
  })
  if (amount) params.set('am', amount)
  if (note) params.set('tn', note)
  return `upi://pay?${params.toString()}`
}
