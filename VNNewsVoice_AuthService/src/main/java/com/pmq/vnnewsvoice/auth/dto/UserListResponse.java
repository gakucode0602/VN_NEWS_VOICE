package com.pmq.vnnewsvoice.auth.dto;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserListResponse {
  private List<AdminUserDto> users;
  private long totalUsers;
  private int currentPage;
  private int totalPages;
  private int startIndex;
  private int endIndex;
}
