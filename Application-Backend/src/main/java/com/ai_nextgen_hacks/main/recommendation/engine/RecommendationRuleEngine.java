package com.ai_nextgen_hacks.main.recommendation.engine;

import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationStatus;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationType;
import org.springframework.stereotype.Component;

@Component
public class RecommendationRuleEngine {

    public RecommendationEntity evaluate(String shipmentId, Double riskScore, String riskLevel) {
        RecommendationEntity rec = new RecommendationEntity();
        rec.setShipmentId(shipmentId);
        rec.setRiskScore(riskScore);
        rec.setRiskLevel(riskLevel);
        rec.setChannel("WHATSAPP");
        rec.setStatus(RecommendationStatus.CREATED);

        if (riskScore < 0.40) {
            rec.setRecommendationType(RecommendationType.NO_INTERVENTION);
            rec.setReason("LOW_FAILURE_RISK");
        } else if (riskScore < 0.70) {
            // Evaluate medium risk conditions
            rec.setRecommendationType(RecommendationType.NO_INTERVENTION); // default
            rec.setReason("MEDIUM_FAILURE_RISK_NO_ACTION");
        } else {
            rec.setRecommendationType(RecommendationType.CONFIRM_AVAILABILITY);
            rec.setReason("HIGH_FAILURE_RISK");
        }
        return rec;
    }
}
