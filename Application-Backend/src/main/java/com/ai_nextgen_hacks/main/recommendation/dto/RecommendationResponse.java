package com.ai_nextgen_hacks.main.recommendation.dto;

import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationStatus;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationType;

public record RecommendationResponse(
    Long id, String shipmentId, Double riskScore, String riskLevel,
    RecommendationType recommendationType, String reason, String channel, RecommendationStatus status
) {
    public static RecommendationResponse fromEntity(RecommendationEntity e) {
        return new RecommendationResponse(e.getId(), e.getShipmentId(), e.getRiskScore(), e.getRiskLevel(),
            e.getRecommendationType(), e.getReason(), e.getChannel(), e.getStatus());
    }
}
