/**
 * DiagnosisResult - Shows the problem type classification result.
 *
 * Displays:
 * - Primary problem type with color-coded indicator
 * - Description and key question
 * - Recommended frameworks as tags
 * - Secondary type (if detected)
 * - Confidence score
 */
export default function DiagnosisResult() {
  const {
    problemType = "undefined",
    problemName = "Un-Defined Problem",
    description = "",
    icon = "\u{1F30A}",
    color = "#E63946",
    keyQuestion = "",
    frameworks = [],
    confidence = 0,
    secondaryName = null,
    secondaryIcon = null,
    secondaryColor = null,
    complexity = "high",
  } = props || {}

  return (
    <Card
      style={{
        background: `linear-gradient(135deg, ${color}10, transparent)`,
        border: `1px solid ${color}40`,
      }}
    >
      <CardHeader>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 32 }}>{icon}</span>
          <div>
            <CardDescription
              style={{
                color: color,
                textTransform: "uppercase",
                letterSpacing: 2,
                fontSize: 11,
              }}
            >
              Your Problem Type
            </CardDescription>
            <CardTitle style={{ fontSize: 22, fontWeight: 400 }}>{problemName}</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p style={{ opacity: 0.7, lineHeight: 1.6, marginBottom: 16 }}>{description}</p>

        {/* Key Question */}
        <div style={{ marginBottom: 16 }}>
          <CardDescription
            style={{ textTransform: "uppercase", letterSpacing: 1, fontSize: 11, marginBottom: 8 }}
          >
            Key Question
          </CardDescription>
          <div
            style={{
              fontStyle: "italic",
              fontSize: 15,
              color: color,
              padding: "12px 16px",
              background: "rgba(0,0,0,0.15)",
              borderRadius: 8,
              borderLeft: `3px solid ${color}`,
            }}
          >
            &ldquo;{keyQuestion}&rdquo;
          </div>
        </div>

        {/* Frameworks */}
        <div style={{ marginBottom: 16 }}>
          <CardDescription
            style={{ textTransform: "uppercase", letterSpacing: 1, fontSize: 11, marginBottom: 8 }}
          >
            Recommended Frameworks
          </CardDescription>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {frameworks.map((f, i) => (
              <Badge
                key={i}
                variant="outline"
                style={{
                  background: `${color}15`,
                  color: color,
                  borderColor: `${color}30`,
                  fontSize: 11,
                }}
              >
                {f}
              </Badge>
            ))}
          </div>
        </div>

        {/* Confidence + Complexity */}
        <div style={{ display: "flex", gap: 16, opacity: 0.5, fontSize: 12 }}>
          <span>Complexity: {complexity}</span>
          {confidence > 0 && <span>Confidence: {Math.round(confidence * 100)}%</span>}
        </div>

        {/* Secondary type */}
        {secondaryName && (
          <div
            style={{
              marginTop: 12,
              paddingTop: 12,
              borderTop: "1px solid rgba(255,255,255,0.08)",
              fontSize: 12,
              opacity: 0.6,
            }}
          >
            Also shows characteristics of:{" "}
            <span style={{ color: secondaryColor || "#F4A261" }}>
              {secondaryIcon} {secondaryName}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
