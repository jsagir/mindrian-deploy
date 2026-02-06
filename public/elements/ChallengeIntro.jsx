/**
 * ChallengeIntro - PWS Consultant Challenge Capture
 *
 * First screen of the PWS Consultant flow:
 * - Multi-line textarea for describing the challenge
 * - "Begin Diagnosis" button to start the 5-question diagnostic
 * - Optional: 4 problem type cards for users who already know their type
 */
export default function ChallengeIntro() {
  const { callAction } = window.Chainlit || {}
  const {
    placeholder = "Describe your problem or challenge...\n\nFor example:\n- What situation are you facing?\n- What have you tried so far?\n- What's at stake if this isn't resolved?",
    showDirectSelect = true,
  } = props || {}

  const [challenge, setChallenge] = React.useState("")
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  // Problem type cards for direct selection
  const problemTypes = [
    {
      id: "undefined",
      name: "Un-Defined",
      icon: "\u{1F30A}",
      color: "#E63946",
      hint: "New territory, many unknowns",
    },
    {
      id: "illdefined",
      name: "Ill-Defined",
      icon: "\u{1F32B}",
      color: "#F4A261",
      hint: "Problem exists but unclear shape",
    },
    {
      id: "welldefined",
      name: "Well-Defined",
      icon: "\u{1F3AF}",
      color: "#2A9D8F",
      hint: "Clear problem, seeking solutions",
    },
    {
      id: "wicked",
      name: "Wicked",
      icon: "\u{1F300}",
      color: "#9D4EDD",
      hint: "Complex, interdependent, no clear solution",
    },
  ]

  const handleSubmitChallenge = () => {
    if (!challenge.trim() || isSubmitting) return
    setIsSubmitting(true)
    if (callAction) {
      callAction({
        name: "submit_challenge",
        payload: {
          challenge: challenge.trim(),
        },
      })
    }
  }

  const handleDirectSelect = (typeId) => {
    if (isSubmitting) return
    setIsSubmitting(true)
    if (callAction) {
      callAction({
        name: "direct_select_type",
        payload: {
          problemType: typeId,
          challenge: challenge.trim() || "",
        },
      })
    }
  }

  return (
    <Card
      style={{
        background: "linear-gradient(135deg, rgba(230,57,70,0.03), rgba(42,157,143,0.03))",
        border: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <CardHeader>
        <CardDescription
          style={{
            textTransform: "uppercase",
            letterSpacing: 2,
            fontSize: 11,
            marginBottom: 4,
          }}
        >
          PWS Consultant
        </CardDescription>
        <CardTitle style={{ fontSize: 20, fontWeight: 400 }}>
          What challenge are you working on?
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Challenge textarea */}
        <textarea
          value={challenge}
          onChange={(e) => setChallenge(e.target.value)}
          placeholder={placeholder}
          disabled={isSubmitting}
          style={{
            width: "100%",
            minHeight: 140,
            padding: 16,
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(0,0,0,0.2)",
            color: "inherit",
            fontFamily: "inherit",
            fontSize: 14,
            lineHeight: 1.6,
            resize: "vertical",
            outline: "none",
          }}
        />

        {/* Submit button */}
        <Button
          onClick={handleSubmitChallenge}
          disabled={!challenge.trim() || isSubmitting}
          style={{
            marginTop: 16,
            width: "100%",
            background: challenge.trim() ? "linear-gradient(135deg, #E63946, #F4A261)" : undefined,
            opacity: challenge.trim() ? 1 : 0.5,
          }}
        >
          {isSubmitting ? "Starting..." : "\u{1F3AF} Begin Diagnosis"}
        </Button>

        {/* Direct select section */}
        {showDirectSelect && (
          <>
            <div
              style={{
                marginTop: 24,
                marginBottom: 12,
                textAlign: "center",
                fontSize: 12,
                opacity: 0.5,
              }}
            >
              Or if you already know your problem type:
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: 8,
              }}
            >
              {problemTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => handleDirectSelect(type.id)}
                  disabled={isSubmitting}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    padding: "12px 8px",
                    borderRadius: 8,
                    border: `1px solid ${type.color}30`,
                    background: `${type.color}08`,
                    cursor: isSubmitting ? "not-allowed" : "pointer",
                    opacity: isSubmitting ? 0.5 : 0.7,
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (!isSubmitting) {
                      e.target.style.opacity = 1
                      e.target.style.background = `${type.color}15`
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.opacity = 0.7
                    e.target.style.background = `${type.color}08`
                  }}
                >
                  <span style={{ fontSize: 20, marginBottom: 4 }}>{type.icon}</span>
                  <span style={{ fontSize: 12, fontWeight: 500, color: type.color }}>
                    {type.name}
                  </span>
                  <span style={{ fontSize: 10, opacity: 0.6, marginTop: 2, textAlign: "center" }}>
                    {type.hint}
                  </span>
                </button>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
