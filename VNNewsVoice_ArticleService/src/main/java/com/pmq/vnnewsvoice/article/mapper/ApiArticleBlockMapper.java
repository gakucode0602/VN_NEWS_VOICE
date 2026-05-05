package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.ArticleBlockResponse;
import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface ApiArticleBlockMapper {
  ArticleBlockResponse toResponse(ArticleBlock articleBlock);
}
