package com.ai_nextgen_hacks.main.recommendation.service;

import com.ai_nextgen_hacks.main.recommendation.enums.RecommendationType;
import org.springframework.stereotype.Service;

@Service
public class RecommendationMessageService {
    public String generateMessage(RecommendationType type, String shipmentId) {
        if (type == RecommendationType.CONFIRM_AVAILABILITY) {
            return "Hello! Your delivery for package " + shipmentId + " is scheduled for today. We want to make sure someone is available to receive your package.\n\nPlease reply:\nYES - I will be available\nRESCHEDULE - I need another day\nPICKUP - I prefer pickup";
        }
        return null;
    }
}
