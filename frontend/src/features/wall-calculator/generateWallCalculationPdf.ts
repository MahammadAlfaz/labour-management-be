import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import type { WallCalculation } from './api'

const BRAND_COLOR: [number, number, number] = [30, 41, 59] // slate-800
const HIGHLIGHT_COLOR: [number, number, number] = [16, 122, 87] // emerald-ish for money
const LIGHT_BORDER: [number, number, number] = [226, 232, 240] // slate-200

function formatNumber(value: string | number): string {
  return Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
}

function formatCurrency(value: string | number): string {
  return `Rs. ${formatNumber(value)}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

/**
 * Builds a client-facing PDF proof of a wall calculation. Purely a
 * data-to-PDF transcription -- no external calls, no LLM involved.
 */
export function buildWallCalculationPdf(calculation: WallCalculation, siteName?: string | null): jsPDF {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const pageWidth = doc.internal.pageSize.getWidth()
  const margin = 40
  let y = 50

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(18)
  doc.setTextColor(...BRAND_COLOR)
  doc.text('Wall Calculation Summary', margin, y)

  y += 22
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(100, 116, 139)
  doc.text(`Generated on ${formatDate(new Date().toISOString())}`, margin, y)

  y += 24
  doc.setDrawColor(...LIGHT_BORDER)
  doc.line(margin, y, pageWidth - margin, y)

  y += 26
  const infoRows: Array<[string, string]> = [
    ['Title', calculation.title || 'Untitled calculation'],
    ['Site', siteName || 'Not linked to a site'],
    ['Date recorded', formatDate(calculation.created_at)],
  ]
  doc.setFontSize(11)
  for (const [label, value] of infoRows) {
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(...BRAND_COLOR)
    doc.text(`${label}:`, margin, y)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(51, 65, 85)
    doc.text(value, margin + 100, y)
    y += 18
  }

  y += 8

  const includedMeasurements = calculation.measurements.filter((m) => m.included)
  if (includedMeasurements.length > 0) {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(...BRAND_COLOR)
    doc.text('Measurements', margin, y)
    y += 8

    autoTable(doc, {
      startY: y,
      margin: { left: margin, right: margin },
      head: [['Description', 'Length (ft)', 'Qty', 'Subtotal (ft)']],
      body: includedMeasurements.map((m) => [
        m.raw_text || '-',
        formatNumber(m.length),
        String(m.quantity),
        formatNumber(Number(m.length) * m.quantity),
      ]),
      theme: 'grid',
      headStyles: { fillColor: BRAND_COLOR, textColor: 255, fontStyle: 'bold' },
      styles: { fontSize: 10, cellPadding: 6, textColor: [51, 65, 85] },
      alternateRowStyles: { fillColor: [248, 250, 252] },
    })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    y = (doc as any).lastAutoTable.finalY + 24
  }

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(...BRAND_COLOR)
  doc.text('Layers', margin, y)
  y += 8

  autoTable(doc, {
    startY: y,
    margin: { left: margin, right: margin },
    head: [['Layer', 'Height (ft)', 'Breadth (ft)', 'Area (sq.ft)']],
    body: calculation.layers.map((l) => [
      l.label || '-',
      formatNumber(l.height),
      formatNumber(l.breadth),
      formatNumber(l.area),
    ]),
    theme: 'grid',
    headStyles: { fillColor: BRAND_COLOR, textColor: 255, fontStyle: 'bold' },
    styles: { fontSize: 10, cellPadding: 6, textColor: [51, 65, 85] },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    columnStyles: { 3: { fontStyle: 'bold' } },
  })
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  y = (doc as any).lastAutoTable.finalY + 32

  // Highlighted summary box -- the key figures a client cares about.
  const boxHeight = 128
  if (y + boxHeight > doc.internal.pageSize.getHeight() - margin) {
    doc.addPage()
    y = 50
  }
  doc.setFillColor(240, 253, 250)
  doc.setDrawColor(...HIGHLIGHT_COLOR)
  doc.roundedRect(margin, y, pageWidth - margin * 2, boxHeight, 8, 8, 'FD')

  const boxPadding = 20
  let boxY = y + boxPadding + 6

  const summaryRows: Array<[string, string, boolean]> = [
    ['Total measurement', `${formatNumber(calculation.total_measurement)} ft`, false],
    ['Total area', `${formatNumber(calculation.total_area)} sq.ft`, false],
    ['Rate per sq.ft', formatCurrency(calculation.rate_per_sqft), false],
    ['Total cost', formatCurrency(calculation.total_cost), true],
  ]

  const bodyTextColor: [number, number, number] = [51, 65, 85]
  for (const [label, value, isTotal] of summaryRows) {
    doc.setFont('helvetica', isTotal ? 'bold' : 'normal')
    doc.setFontSize(isTotal ? 15 : 11)
    doc.setTextColor(...(isTotal ? HIGHLIGHT_COLOR : bodyTextColor))
    doc.text(label, margin + boxPadding, boxY)
    doc.text(value, pageWidth - margin - boxPadding, boxY, { align: 'right' })
    boxY += isTotal ? 26 : 20
  }

  doc.setFontSize(8)
  doc.setTextColor(148, 163, 184)
  doc.text(
    'This is a computer-generated measurement and cost summary.',
    margin,
    doc.internal.pageSize.getHeight() - 24
  )

  return doc
}

/** Builds the PDF proof and triggers a browser download. */
export function generateWallCalculationPdf(calculation: WallCalculation, siteName?: string | null): void {
  const doc = buildWallCalculationPdf(calculation, siteName)
  const safeTitle = (calculation.title || 'wall-calculation').replace(/[^a-z0-9-]+/gi, '-').toLowerCase()
  doc.save(`${safeTitle}-${calculation.id.slice(-6)}.pdf`)
}
