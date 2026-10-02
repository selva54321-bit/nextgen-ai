package com.ai_nextgen_hacks.main.recommendation.entity;

import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationStatus;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationType;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "recommendations")
public class RecommendationEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String shipmentId;
    private Double riskScore;
    private String riskLevel;
    @Enumerated(EnumType.STRING)
    private RecommendationType recommendationType;
    private String reason;
    private String channel;
    @Enumerated(EnumType.STRING)
    private RecommendationStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist protected void onCreate() { createdAt = LocalDateTime.now(); updatedAt = LocalDateTime.now(); }
    @PreUpdate protected void onUpdate() { updatedAt = LocalDateTime.now(); }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getShipmentId() { return shipmentId; }
    public void setShipmentId(String shipmentId) { this.shipmentId = shipmentId; }
    public Double getRiskScore() { return riskScore; }
    public void setRiskScore(Double riskScore) { this.riskScore = riskScore; }
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    public RecommendationType getRecommendationType() { return recommendationType; }
    public void setRecommendationType(RecommendationType recommendationType) { this.recommendationType = recommendationType; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
    public String getChannel() { return channel; }
    public void setChannel(String channel) { this.channel = channel; }
    public RecommendationStatus getStatus() { return status; }
    public void setStatus(RecommendationStatus status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
