package com.pmq.vnnewsvoice.article.dto;

import java.util.Date;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleLikeDto {
  private Long id;
  private Date createdAt;
  private UUID articleIdId;
  private String articleIdTitle;
  private String articleIdSlug;
  // readerId stores UserInfo.id from JWT — no Reader entity reference
  private Long readerId;
}
