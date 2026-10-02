package com.ai_nextgen_hacks.main.recommendation.service;

import com.ai_nextgen_hacks.main.recommendation.engine.RecommendationRuleEngine;
import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationStatus;
import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationType;
import com.ai_nextgen_hacks.main.recommendation.repository.RecommendationRepository;
import com.ai_nextgen_hacks.main.whatsapp.service.WhatsAppService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RecommendationService {

    @Autowired private RecommendationRuleEngine ruleEngine;
    @Autowired private RecommendationRepository recommendationRepository;
    @Autowired private RecommendationMessageService messageService;
    @Autowired private WhatsAppService whatsAppService;

    public RecommendationEntity generateRecommendation(String shipmentId, Double riskScore, String riskLevel, String customerPhone) {
        RecommendationEntity rec = ruleEngine.evaluate(shipmentId, riskScore, riskLevel);
        recommendationRepository.save(rec);

        if (rec.getRecommendationType() != RecommendationType.NO_INTERVENTION) {
            String message = messageService.generateMessage(rec.getRecommendationType(), shipmentId);
            if (message != null && customerPhone != null) {
                whatsAppService.sendMessage(customerPhone, message, rec);
                rec.setStatus(RecommendationStatus.SENT);
                recommendationRepository.save(rec);
            }
        }
        return rec;
    }

    public List<RecommendationEntity> getHistory(String shipmentId) {
        return recommendationRepository.findByShipmentIdOrderByCreatedAtDesc(shipmentId);
    }
}
