package com.ai_nextgen_hacks.main.recommendation.controller;

import com.ai_nextgen_hacks.main.recommendation.dto.RecommendationResponse;
import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import com.ai_nextgen_hacks.main.recommendation.service.RecommendationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.stream.Collectors;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/recommendations")
public class RecommendationController {

    @Autowired private RecommendationService recommendationService;

    @PostMapping("/{shipmentId}")
    public ResponseEntity<RecommendationResponse> createRecommendation(@PathVariable String shipmentId, @RequestBody Map<String, Object> body) {
        Double riskScore = Double.parseDouble(body.getOrDefault("riskScore", "0.0").toString());
        String riskLevel = (String) body.getOrDefault("riskLevel", "UNKNOWN");
        String phone = (String) body.get("phoneNumber"); // Pass customer phone for testing
        RecommendationEntity rec = recommendationService.generateRecommendation(shipmentId, riskScore, riskLevel, phone);
        return ResponseEntity.ok(RecommendationResponse.fromEntity(rec));
    }

    @GetMapping("/{shipmentId}")
    public ResponseEntity<List<RecommendationResponse>> getRecommendations(@PathVariable String shipmentId) {
        List<RecommendationResponse> list = recommendationService.getHistory(shipmentId)
            .stream().map(RecommendationResponse::fromEntity).collect(Collectors.toList());
        return ResponseEntity.ok(list);
    }
}
