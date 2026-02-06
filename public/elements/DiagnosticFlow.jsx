/**
 * DiagnosticFlow - PWS Problem Type Diagnostic
 *
 * A structured 5-question diagnostic that classifies problems into:
 * Un-Defined, Ill-Defined, Well-Defined, or Wicked.
 *
 * Each answer triggers a callAction back to Python which scores
 * and advances to the next question (or completes).
 */
export default function DiagnosticFlow() {
  const { callAction } = window.Chainlit || {}
  const {
    question = "",
    options = [],
    questionNumber = 1,
    totalQuestions = 5,
    questionId = "clarity",
  } = props || {}

  const progress = (questionNumber / totalQuestions) * 100

  const handleAnswer = (optionIndex, optionLabel) => {
    if (callAction) {
      callAction({
        name: "diagnostic_answer",
        payload: {
          questionId: questionId,
          optionIndex: optionIndex,
          optionLabel: optionLabel,
          questionNumber: questionNumber,
        },
      })
    }
  }

  return (
    <Card
      style={{
        background: "linear-gradient(135deg, rgba(230,57,70,0.05), rgba(42,157,143,0.05))",
        border: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <CardHeader style={{ paddingBottom: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <CardDescription style={{ textTransform: "uppercase", letterSpacing: 2, fontSize: 11 }}>
            Problem Diagnostic
          </CardDescription>
          <span style={{ fontFamily: "monospace", fontSize: 12, opacity: 0.5 }}>
            {questionNumber}/{totalQuestions}
          </span>
        </div>
        {/* Progress bar */}
        <div
          style={{
            height: 2,
            background: "rgba(255,255,255,0.08)",
            borderRadius: 1,
            marginTop: 8,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progress}%`,
              background: "linear-gradient(90deg, #E63946, #F4A261, #2A9D8F)",
              borderRadius: 1,
              transition: "width 0.5s ease",
            }}
          />
        </div>
      </CardHeader>
      <CardContent>
        <CardTitle style={{ fontSize: 18, fontWeight: 400, marginBottom: 16, lineHeight: 1.4 }}>
          {question}
        </CardTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {options.map((opt, i) => (
            <Button
              key={i}
              variant="outline"
              style={{
                justifyContent: "flex-start",
                textAlign: "left",
                height: "auto",
                padding: "12px 16px",
                whiteSpace: "normal",
                lineHeight: 1.5,
              }}
              onClick={() => handleAnswer(i, opt)}
            >
              {opt}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
