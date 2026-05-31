/**
 * Convert backend session events to frontend message objects.
 * Shared between TextMode and InterviewSummaryPage.
 */
export function eventsToMessages(events) {
  const result = []
  for (const event of events) {
    if (event.type === 'user.text') {
      const text = (event.payload?.text || '').trim()
      if (text) result.push({ role: 'user', content: text })
    } else if (event.type === 'assistant.text.done') {
      const text = event.payload?.text || ''
      if (text) result.push({ role: 'ai', content: text })
    }
  }
  return result
}
