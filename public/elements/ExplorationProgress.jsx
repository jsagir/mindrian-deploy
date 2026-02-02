/**
 * ExplorationProgress - Sandbox Depth Tracker (SIDEBAR)
 *
 * Shows exploration progress in sandbox mode:
 * - Depth levels: Initial → Exploring → Deep → Synthesis
 * - Topics explored (from LangExtract)
 * - Sources consulted
 * - Grounding score
 * - Opportunities banked
 *
 * FIXED: display="side" - persists in sidebar
 * FIXED: Updates via updateElement without re-sending
 */

export default function ExplorationProgress() {
    const {
        depth = "initial",
        topicsExplored = [],
        sourcesConsulted = 0,
        groundingScore = 0,
        opportunitiesBanked = 0,
        lastGroundingReason = null
    } = props || {};

    const depths = [
        { id: "initial", label: "Initial", icon: "🌱", color: "#d1d5db" },
        { id: "exploring", label: "Exploring", icon: "🔍", color: "#60a5fa" },
        { id: "deep", label: "Deep", icon: "🏊", color: "#8b5cf6" },
        { id: "synthesis", label: "Synthesis", icon: "🧩", color: "#10b981" }
    ];

    const currentIndex = depths.findIndex(d => d.id === depth);
    const currentDepth = depths[currentIndex] || depths[0];

    const styles = {
        container: {
            padding: '16px',
            backgroundColor: '#1e293b',
            borderRadius: '12px',
            border: '1px solid #334155',
            color: '#f8fafc',
        },
        header: {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px',
            fontWeight: '600',
            fontSize: '14px',
        },
        progressBar: {
            display: 'flex',
            gap: '4px',
            marginBottom: '8px',
        },
        progressSegment: {
            flex: 1,
            height: '6px',
            borderRadius: '3px',
            transition: 'background-color 0.3s ease',
        },
        depthLabel: {
            textAlign: 'center',
            fontSize: '13px',
            color: '#94a3b8',
            marginBottom: '16px',
        },
        statsGrid: {
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '8px',
        },
        statCard: {
            padding: '10px',
            backgroundColor: '#334155',
            borderRadius: '8px',
            textAlign: 'center',
        },
        statValue: {
            fontSize: '18px',
            fontWeight: '600',
            color: '#f8fafc',
        },
        statLabel: {
            fontSize: '11px',
            color: '#94a3b8',
            marginTop: '2px',
        },
        topicsSection: {
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px solid #334155',
        },
        topicsLabel: {
            fontSize: '11px',
            color: '#94a3b8',
            marginBottom: '6px',
        },
        topicTags: {
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px',
        },
        topicTag: {
            padding: '3px 8px',
            backgroundColor: '#3b82f620',
            color: '#60a5fa',
            borderRadius: '4px',
            fontSize: '11px',
        },
        moreTag: {
            padding: '3px 8px',
            backgroundColor: '#475569',
            color: '#94a3b8',
            borderRadius: '4px',
            fontSize: '11px',
        },
        groundingHint: {
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#f59e0b20',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#fbbf24',
            textAlign: 'center',
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                🧠 Exploration Progress
            </div>

            {/* Depth Progress Bar */}
            <div style={styles.progressBar}>
                {depths.map((d, i) => (
                    <div
                        key={d.id}
                        style={{
                            ...styles.progressSegment,
                            backgroundColor: i <= currentIndex ? d.color : '#475569'
                        }}
                        title={d.label}
                    />
                ))}
            </div>

            <div style={styles.depthLabel}>
                {currentDepth.icon} {currentDepth.label}
            </div>

            {/* Stats Grid */}
            <div style={styles.statsGrid}>
                <div style={styles.statCard}>
                    <div style={styles.statValue}>{topicsExplored.length}</div>
                    <div style={styles.statLabel}>Topics</div>
                </div>
                <div style={styles.statCard}>
                    <div style={styles.statValue}>{sourcesConsulted}</div>
                    <div style={styles.statLabel}>Sources</div>
                </div>
                <div style={styles.statCard}>
                    <div style={styles.statValue}>{Math.round(groundingScore * 100)}%</div>
                    <div style={styles.statLabel}>Grounded</div>
                </div>
                <div style={styles.statCard}>
                    <div style={styles.statValue}>{opportunitiesBanked}</div>
                    <div style={styles.statLabel}>Banked</div>
                </div>
            </div>

            {/* Topics List */}
            {topicsExplored.length > 0 && (
                <div style={styles.topicsSection}>
                    <div style={styles.topicsLabel}>Topics explored:</div>
                    <div style={styles.topicTags}>
                        {topicsExplored.slice(0, 6).map((topic, i) => (
                            <span key={i} style={styles.topicTag}>{topic}</span>
                        ))}
                        {topicsExplored.length > 6 && (
                            <span style={styles.moreTag}>
                                +{topicsExplored.length - 6} more
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Grounding hint */}
            {lastGroundingReason && (
                <div style={styles.groundingHint}>
                    💡 {lastGroundingReason === 'pattern_check' ? 'Patterns emerging...' :
                        lastGroundingReason === 'synthesis' ? 'Ready to synthesize?' :
                        'Consider banking an insight'}
                </div>
            )}
        </div>
    );
}
