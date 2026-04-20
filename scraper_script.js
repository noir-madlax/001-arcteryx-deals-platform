
// Arc'teryx 完整数据抓取脚本
// 这个脚本需要在浏览器控制台中运行

(async function() {
  console.log("开始抓取始祖鸟数据...");
  
  // 存储所有产品的数组
  const allProducts = [];
  
  // 定义需要抓取的页面
  const pages = [
    {url: 'https://outlet.arcteryx.com/us/en/c/mens', region: 'us', region_name: '美国', currency: 'USD', symbol: '$'},
    {url: 'https://outlet.arcteryx.com/us/en/c/womens', region: 'us', region_name: '美国', currency: 'USD', symbol: '$'},
    {url: 'https://outlet.arcteryx.com/ca/en/c/mens', region: 'ca', region_name: '加拿大', currency: 'CAD', symbol: 'C$'},
    {url: 'https://outlet.arcteryx.com/ca/en/c/womens', region: 'ca', region_name: '加拿大', currency: 'CAD', symbol: 'C$'},
    {url: 'https://outlet.arcteryx.com/de/en/c/mens', region: 'de', region_name: '德国', currency: 'EUR', symbol: '€'},
    {url: 'https://outlet.arcteryx.com/de/en/c/womens', region: 'de', region_name: '德国', currency: 'EUR', symbol: '€'},
    {url: 'https://outlet.arcteryx.com/gb/en/c/mens', region: 'gb', region_name: '英国', currency: 'GBP', symbol: '£'},
    {url: 'https://outlet.arcteryx.com/gb/en/c/womens', region: 'gb', region_name: '英国', currency: 'GBP', symbol: '£'},
    {url: 'https://outlet.arcteryx.com/fr/en/c/mens', region: 'fr', region_name: '法国', currency: 'EUR', symbol: '€'},
    {url: 'https://outlet.arcteryx.com/fr/en/c/womens', region: 'fr', region_name: '法国', currency: 'EUR', symbol: '€'},
    {url: 'https://outlet.arcteryx.com/nl/en/c/mens', region: 'nl', region_name: '荷兰', currency: 'EUR', symbol: '€'},
    {url: 'https://outlet.arcteryx.com/nl/en/c/womens', region: 'nl', region_name: '荷兰', currency: 'EUR', symbol: '€'},
  ];
  
  // 抓取单个页面的函数
  async function scrapePage(pageInfo) {
    console.log(`抓取页面: ${pageInfo.url}`);
    
    // 导航到页面
    window.location.href = pageInfo.url;
    
    // 等待页面加载
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 滚动页面以加载所有产品
    for (let i = 0; i < 20; i++) {
      window.scrollTo(0, document.body.scrollHeight);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // 等待图片加载
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 抓取产品
    const products = [];
    const imgs = document.querySelectorAll('img[alt*="Men\'s"], img[alt*="Women\'s"]');
    const seen = new Set();
    
    imgs.forEach(img => {
      const name = img.alt;
      if (seen.has(name)) return;
      seen.add(name);
      
      const imgUrl = img.dataset?.src || img.src;
      if (!imgUrl || !imgUrl.includes('imgix.net')) return;
      
      // 查找父级元素中的链接和价格
      let parent = img.parentElement;
      for (let i = 0; i < 10 && parent; i++) {
        const link = parent.querySelector('a[href*="/shop/"]');
        const priceEls = parent.querySelectorAll('[class*="price"], [class*="Price"]');
        
        if (link && priceEls.length > 0) {
          const prices = [];
          priceEls.forEach(p => {
            const matches = p.textContent.match(/[\$€£][\d,.]+/g);
            if (matches) prices.push(...matches);
          });
          
          if (prices.length >= 2) {
            const href = link.getAttribute('href');
            const slug = href.split('/').pop();
            
            // 解析价格
            const originalPrice = parseFloat(prices[0].replace(/[^\d.]/g, ''));
            const salePrice = parseFloat(prices[1].replace(/[^\d.]/g, ''));
            const discountPct = Math.round((1 - salePrice / originalPrice) * 100);
            
            products.push({
              model: name,
              full_name: name,
              description: '',
              category: name.includes('Shoe') ? '鞋类' : 
                       name.includes('Jacket') ? '外套' :
                       name.includes('Pant') ? '裤装' :
                       name.includes('Shirt') ? '上衣' :
                       name.includes('Hoody') ? '卫衣' : '其他',
              original_price: originalPrice,
              sale_price: salePrice,
              sale_price_max: salePrice,
              discount_pct: discountPct,
              currency: pageInfo.currency,
              symbol: pageInfo.symbol,
              gender: name.includes('Men\'s') ? 'men' : 'women',
              region: pageInfo.region,
              region_name: pageInfo.region_name,
              url: 'https://outlet.arcteryx.com' + href,
              image_url: imgUrl.split('?')[0],
              last_updated: new Date().toISOString(),
              colors: [],
              sizes: [],
              size_stock: {}
            });
          }
          break;
        }
        parent = parent.parentElement;
      }
    });
    
    console.log(`抓取到 ${products.length} 个产品`);
    return products;
  }
  
  // 抓取所有页面
  for (const page of pages) {
    try {
      const products = await scrapePage(page);
      allProducts.push(...products);
    } catch (error) {
      console.error(`抓取页面失败: ${page.url}`, error);
    }
  }
  
  // 保存到全局变量
  window.__allScrapedProducts = allProducts;
  
  console.log(`\n抓取完成！总共 ${allProducts.length} 个产品`);
  console.log("请运行以下命令导出数据：");
  console.log("JSON.stringify(window.__allScrapedProducts, null, 2)");
  
  return allProducts;
})();
