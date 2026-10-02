package com.ai_nextgen_hacks.main.repos;

import com.ai_nextgen_hacks.main.models.DispatchAssignment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DispatchAssignmentRepository extends JpaRepository<DispatchAssignment, String> {
}
