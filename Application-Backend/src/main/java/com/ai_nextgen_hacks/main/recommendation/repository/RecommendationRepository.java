package com.ai_nextgen_hacks.main.recommendation.repository;

import com.ai_nextgen_hacks.main.recommendation.entity.RecommendationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface RecommendationRepository extends JpaRepository<RecommendationEntity, Long> {
    List<RecommendationEntity> findByShipmentIdOrderByCreatedAtDesc(String shipmentId);
}
