/**
 * ExpertPanel - Domain-specific consulting experts built by background pipeline.
 *
 * Shows experts as interactive cards that the user can click to "consult".
 * Each expert is grounded in the user's actual domain + subdomain,
 * built by the BONO expert-builder pipeline.
 *
 * Clicking an expert triggers consult_expert action callback.
 */
export default function ExpertPanel() {
  const { callAction } = window.Chainlit || {}
  const {
    experts = [],
    domain = "",
    title = "Your Consulting Panel",
    subtitle = "Domain specialists ready to offer their perspective",
    loading = false,
    loadingMessage = "Building your expert panel...",
  } = props || {}

  const handleConsult = (expert) => {
    if (callAction) {
      callAction({
        name: "consult_expert",
        payload: {
          expertId: expert.id,
          role: expert.role,
          subdomain: expert.subdomain,
          systemContext: expert.system_context || "",
          approach: expert.approach || "",
        },
      })
    }
  }

  if (loading) {
    return (
      <Card style={{ border: "1px solid rgba(255,255,255,0.08)" }}>
        <CardContent style={{ padding: 24, textAlign: "center" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "#F4A261",
                animation: "pulse 1.2s ease infinite",
              }}
            />
            <span style={{ opacity: 0.5, fontSize: 13 }}>{loadingMessage}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (experts.length === 0) return null

  return (
    <Card style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
      <CardHeader style={{ paddingBottom: 8 }}>
        <CardTitle style={{ fontSize: 16 }}>{title}</CardTitle>
        <CardDescription>{subtitle}</CardDescription>
        {domain && (
          <Badge variant="outline" style={{ marginTop: 4, fontSize: 11 }}>
            {domain}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {experts.map((expert) => (
            <Button
              key={expert.id}
              variant="outline"
              style={{
                height: "auto",
                padding: "14px 12px",
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                gap: 4,
                textAlign: "left",
                borderColor: `${expert.color || "#666"}30`,
                background: `${expert.color || "#666"}08`,
              }}
              onClick={() => handleConsult(expert)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, width: "100%" }}>
                <span style={{ fontSize: 20 }}>{expert.icon}</span>
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: expert.color || "#E8E8E8",
                  }}
                >
                  {expert.role}
                </span>
              </div>
              <span
                style={{
                  fontSize: 11,
                  opacity: 0.5,
                  whiteSpace: "normal",
                  lineHeight: 1.4,
                }}
              >
                {expert.subdomain}
              </span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
