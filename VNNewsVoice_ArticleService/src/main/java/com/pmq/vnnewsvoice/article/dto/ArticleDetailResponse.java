package com.pmq.vnnewsvoice.article.dto;

import java.util.List;
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
public class ArticleDetailResponse {
  private ArticleResponse article;
  private List<ArticleBlockResponse> blocks;
}
