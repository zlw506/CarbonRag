# CarbonRag Carbon Factor Index

This is a compact directory for CarbonRag's local carbon factor registry.
Use it to identify candidate activity names before calling `carbon_factor_lookup` for calculation-ready factor values.

- registry_record_count: 366
- unique_activity_count: 315
- value_source: `carbon_factor_lookup` results, not this index

## Activity Index

| Activity category | Activity name | Records | Activity units | Factor units | Example factor IDs |
| --- | --- | ---: | --- | --- | --- |
| mobile_combustion | diesel_vehicle | 2 | L | kgCO2e/L | factor-demo-diesel-vehicle-l-v1_4_4, factor-cn-guidance-diesel-vehicle-l-v1 |
| mobile_combustion | gasoline_vehicle | 2 | L | kgCO2e/L | factor-demo-gasoline-vehicle-l-v1_4_4, factor-cn-guidance-gasoline-vehicle-l-v1 |
| personal_calculator_clothes | 洗衣液 | 1 | L | kgCO2e/L | carbonstop-calculator-03 |
| personal_calculator_clothes | 涤纶织物 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-01 |
| personal_calculator_clothes | 纯棉T恤 | 1 | 件 | kgCO2e/件 | carbonstop-calculator-02 |
| personal_calculator_daily | 一次性筷子 | 1 | 双 | kgCO2e/双 | carbonstop-calculator-39 |
| personal_calculator_daily | 城市垃圾 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-42 |
| personal_calculator_daily | 塑料袋 | 1 | 个 | kgCO2e/个 | carbonstop-calculator-38 |
| personal_calculator_daily | 洗发水 | 1 | 瓶 | kgCO2e/瓶 | carbonstop-calculator-40 |
| personal_calculator_daily | 玫瑰 | 1 | 支 | kgCO2e/支 | carbonstop-calculator-41 |
| personal_calculator_daily | 纸制品 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-37 |
| personal_calculator_food | 吸烟 | 1 | 包 | kgCO2e/包 | carbonstop-calculator-06 |
| personal_calculator_food | 啤酒 | 1 | 瓶 | kgCO2e/瓶 | carbonstop-calculator-05 |
| personal_calculator_food | 土豆 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-12 |
| personal_calculator_food | 扁豆 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-20 |
| personal_calculator_food | 炸鸡 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-10 |
| personal_calculator_food | 牛奶 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-18 |
| personal_calculator_food | 牛肉 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-08 |
| personal_calculator_food | 猪肉 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-09 |
| personal_calculator_food | 白酒 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-04 |
| personal_calculator_food | 米饭 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-13 |
| personal_calculator_food | 羊肉 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-07 |
| personal_calculator_food | 花生 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-14 |
| personal_calculator_food | 西兰花 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-16 |
| personal_calculator_food | 西红柿 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-19 |
| personal_calculator_food | 豆腐 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-17 |
| personal_calculator_food | 酸奶 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-15 |
| personal_calculator_food | 鸡蛋 | 1 | 千克 | kgCO2e/千克 | carbonstop-calculator-11 |
| personal_calculator_home | 天然气 | 1 | 立方米 | kgCO2e/立方米 | carbonstop-calculator-25 |
| personal_calculator_home | 液化气 | 1 | 立方米 | kgCO2e/立方米 | carbonstop-calculator-28 |
| personal_calculator_home | 煤 | 1 | 吨 | kgCO2e/吨 | carbonstop-calculator-21 |
| personal_calculator_home | 煤气 | 1 | 立方米 | kgCO2e/立方米 | carbonstop-calculator-24 |
| personal_calculator_home | 用水 | 1 | 立方米 | kgCO2e/立方米 | carbonstop-calculator-23 |
| personal_calculator_home | 用电 | 1 | 度 | kgCO2e/度 | carbonstop-calculator-22 |
| personal_calculator_home | 蜂窝煤 | 1 | 块 | kgCO2e/块 | carbonstop-calculator-27 |
| personal_calculator_home | 集中供暖 | 1 | 平米*每天 | kgCO2e/平米*每天 | carbonstop-calculator-26 |
| personal_calculator_travel | 中耗油小汽车 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-35 |
| personal_calculator_travel | 低耗油小汽车 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-36 |
| personal_calculator_travel | 公共汽车 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-33 |
| personal_calculator_travel | 地铁 | 1 | 站 | kgCO2e/站 | carbonstop-calculator-32 |
| personal_calculator_travel | 火车 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-30 |
| personal_calculator_travel | 轮船 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-31 |
| personal_calculator_travel | 飞机 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-29 |
| personal_calculator_travel | 高耗油小汽车 | 1 | 公里 | kgCO2e/公里 | carbonstop-calculator-34 |
| purchased_electricity | electricity | 41 | kWh | kgCO2/kWh | factor-cn-electricity-national-2023-mee-nbs, factor-cn-electricity-national-residual-2023-mee-nbs, factor-cn-electricity-national-fossil-2023-mee-nbs, factor-cn-electricity-grid-north-2023-mee-nbs |
| stationary_combustion | anthracite_coal | 1 | t | kgCO2e/t | factor-cn-guidance-anthracite-coal-t-v1 |
| stationary_combustion | coal | 2 | kg, t | kgCO2e/kg, kgCO2e/t | factor-demo-coal-kg-stationary-v1_4_4, factor-cn-guidance-coal-bituminous-t-v1 |
| stationary_combustion | diesel | 2 | L | kgCO2e/L | factor-demo-diesel-l-stationary-v1_4_4, factor-cn-guidance-diesel-l-v1 |
| stationary_combustion | fuel_oil | 1 | L | kgCO2e/L | factor-cn-guidance-fuel-oil-l-v1 |
| stationary_combustion | gasoline | 2 | L | kgCO2e/L | factor-demo-gasoline-l-stationary-v1_4_4, factor-cn-guidance-gasoline-l-v1 |
| stationary_combustion | kerosene | 1 | L | kgCO2e/L | factor-cn-guidance-kerosene-l-v1 |
| stationary_combustion | lpg | 2 | kg | kgCO2e/kg | factor-demo-lpg-kg-stationary-v1_4_4, factor-cn-guidance-lpg-kg-v1 |
| stationary_combustion | natural_gas | 2 | m3 | kgCO2e/m3 | factor-demo-natural-gas-m3-v1_4_4, factor-cn-guidance-natural-gas-m3-v1 |
| 公共交通 | 公交车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1337960904813568 |
| 公共交通 | 公车运输服务-乙类市区公车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1381768356361984 |
| 公共交通 | 公车运输服务-低地板甲类市区公车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1381768353740544 |
| 公共交通 | 公车运输服务-普通甲类市区公车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1381768358983424 |
| 公共交通 | 南航飞机排放 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1662866295673600 |
| 公共交通 | 普通出租车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1337961197792256 |
| 其他 | C30混凝土 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1381792284210944 |
| 其他 | C50混凝土 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1381792286865152 |
| 其他 | iPod touch-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476795457009920 |
| 其他 | 危险废弃物 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1609534705867776 |
| 其他 | 复印机 | 1 | 台 | tCO₂e/台 | carbonstop-ccdb-1381776716330752 |
| 其他 | 天然石膏 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978292374528 |
| 其他 | 平板玻璃 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978290572288 |
| 其他 | 废弃物焚化处理服务 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1381768369501952 |
| 其他 | 庭院和公园废弃物 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1609534668184576 |
| 其他 | 建材集料（瓦砾、碎石等） | 1 | t | kgCO₂e/t | carbonstop-ccdb-1337962781338624 |
| 其他 | 断桥铝合金窗 | 1 | ㎡ | kgCO₂e/㎡ | carbonstop-ccdb-1279978384944128 |
| 其他 | 有机废弃物免发酵转化肥料处理服务 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1381768584853248 |
| 其他 | 消石灰 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978294209536 |
| 其他 | 混凝土 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1337962792381440 |
| 其他 | 混凝土砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978301484032 |
| 其他 | 炼钢生铁 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978328058880 |
| 其他 | 烧结粉煤灰实心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978312887296 |
| 其他 | 热轧碳钢小型型钢 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978336873472 |
| 其他 | 煤矸石实心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978311150592 |
| 其他 | 煤矸石空心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978309217280 |
| 其他 | 砂 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978286443520 |
| 其他 | 砖 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1337962790611968 |
| 其他 | 碎石 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978288311296 |
| 其他 | 粘土 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978298010624 |
| 其他 | 粘土空心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978307152896 |
| 其他 | 蒸压粉煤灰砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978315017216 |
| 其他 | 铸造生铁 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978329893888 |
| 其他 | 页岩实心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978305350656 |
| 其他 | 页岩石 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1279978296110080 |
| 其他 | 页岩空心砖 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1279978303319040 |
| 农林牧渔 | 哈密瓜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778987092224 |
| 农林牧渔 | 大头菜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779013404928 |
| 农林牧渔 | 大米/米饭 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779339905280 |
| 农林牧渔 | 大麦 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779083593984 |
| 农林牧渔 | 奶油豆 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779061934336 |
| 农林牧渔 | 小麦/面粉 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779152439552 |
| 农林牧渔 | 无花果 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779078842624 |
| 农林牧渔 | 柑橘/橘子 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779100436736 |
| 农林牧渔 | 柚子/葡萄柚 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779139234048 |
| 农林牧渔 | 橄榄 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779169446144 |
| 农林牧渔 | 橘子/柑橘 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779143756032 |
| 农林牧渔 | 洋葱 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778944133376 |
| 农林牧渔 | 燕麦 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779048302848 |
| 农林牧渔 | 牛肉 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779510692096 |
| 农林牧渔 | 玉米 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779109611776 |
| 农林牧渔 | 瓜类 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779135072512 |
| 农林牧渔 | 甜菜根 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778978965760 |
| 农林牧渔 | 胡萝卜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778957502720 |
| 农林牧渔 | 芹菜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778948720896 |
| 农林牧渔 | 苹果 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779008981248 |
| 农林牧渔 | 茴香 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779113707776 |
| 农林牧渔 | 草莓 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779160893696 |
| 农林牧渔 | 菠萝 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779130714368 |
| 农林牧渔 | 蒜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779156437248 |
| 农林牧渔 | 蘑菇 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779000363264 |
| 农林牧渔 | 西兰花 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779165219072 |
| 农林牧渔 | 西红柿 | 2 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779105220864, carbonstop-ccdb-1476778953111808 |
| 农林牧渔 | 西红柿/番茄 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779148081408 |
| 农林牧渔 | 豆子 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779096242432 |
| 农林牧渔 | 豌豆 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779057346816 |
| 农林牧渔 | 黄瓜 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476778970642688 |
| 农林牧渔 | 黑麦 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1476779052529920 |
| 天然气、石油 | 一般煤油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446209201920 |
| 天然气、石油 | 其他洗煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446190032640 |
| 天然气、石油 | 其他煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446248490752 |
| 天然气、石油 | 其他石油制品 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446214772480 |
| 天然气、石油 | 原油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446199437056 |
| 天然气、石油 | 型煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446192031488 |
| 天然气、石油 | 天然气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446232270592 |
| 天然气、石油 | 密闭电石炉炉气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446245705472 |
| 天然气、石油 | 无烟煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446181971712 |
| 天然气、石油 | 柴油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446206318336 |
| 天然气、石油 | 汽油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446203926272 |
| 天然气、石油 | 洗精煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446187935488 |
| 天然气、石油 | 液化天然气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446228928256 |
| 天然气、石油 | 液化石油气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446225913600 |
| 天然气、石油 | 炼厂干气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446223292160 |
| 天然气、石油 | 烟煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446184036096 |
| 天然气、石油 | 焦油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446217721600 |
| 天然气、石油 | 焦炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446234531584 |
| 天然气、石油 | 焦炭 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446194325248 |
| 天然气、石油 | 燃料油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446201566976 |
| 天然气、石油 | 石油焦 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446211757824 |
| 天然气、石油 | 粗苯 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446220736256 |
| 天然气、石油 | 褐煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446186002176 |
| 天然气、石油 | 转炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446242887424 |
| 天然气、石油 | 高炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446237710080 |
| 工业 | 白云石 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413806719488 |
| 工业 | 石灰石 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413810061824 |
| 工业 | 碳酸亚铁 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413787812352 |
| 工业 | 碳酸氢钠 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413789549056 |
| 工业 | 碳酸钙 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413794857472 |
| 工业 | 碳酸钠 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413791252992 |
| 工业 | 碳酸钡 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413784273408 |
| 工业 | 碳酸钾 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413780898304 |
| 工业 | 碳酸锂 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413782602240 |
| 工业 | 碳酸锰 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413786173952 |
| 工业 | 碳酸锶 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413779161600 |
| 工业 | 碳酸镁 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413792989696 |
| 工业 | 碳酸镁钙 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413777490432 |
| 工业 | 纯碱 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413799936512 |
| 工业 | 菱铁矿 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413805015552 |
| 工业 | 菱锰矿 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413801607680 |
| 工业 | 菱镁石 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413808390656 |
| 工业 | 铁白云石 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584413803311616 |
| 平板电脑 | 12.9 英寸 iPad Pro (第五代)-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496484556406016 |
| 平板电脑 | SM-T545 (Galaxy Tab Active Pro)-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496474211745024 |
| 平板电脑 | 平板电脑-HP Elite x2 1012 G2 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476801046804736 |
| 平板电脑 | 平板电脑-华为 MediaPad M5 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476801042315520 |
| 废弃物处理 | 电力废玻璃、陶瓷废料处理 | 1 | kWh | kgCO₂e/kWh | carbonstop-ccdb-1584395250856448 |
| 快递、包装、交通 | 塑料编织布包装袋 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413987041792 |
| 快递、包装、交通 | 塑料薄膜包装袋 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413988712960 |
| 快递、包装、交通 | 快递包装箱 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413990384128 |
| 快递、包装、交通 | 快递封套 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413992055296 |
| 快递、包装、交通 | 运单 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413993693696 |
| 快递、包装、交通 | 透明胶带 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1584413985305088 |
| 手机 | Apple Watch Series 7 (GPS + 蜂窝网络，GPS)-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496484453350656 |
| 手机 | BlackBerry Bold 9900手机 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586267958272 |
| 手机 | BlackBerry Classic手机 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586305059840 |
| 手机 | BlackBerry Passport手机 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586286504960 |
| 手机 | BlackBerry Z10手机 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586277207040 |
| 手机 | Motorola Droid Razr智能手机 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704587331828736 |
| 手机 | SM-A127F (Galaxy A12)-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496474244578560 |
| 手机 | iPhone 13 Pro Max-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496484618206464 |
| 手机 | iPhone SE第二代-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476792926468352 |
| 手机 | iPhone XS-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476792841009408 |
| 手机 | 手机 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776405526272 |
| 机械设备 | 使用燃气或石油的厨房加热设备 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776237557504 |
| 机械设备 | 农业机械 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776301848320 |
| 机械设备 | 建筑和采矿机械 | 2 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776490657536, carbonstop-ccdb-1381776282875648 |
| 机械设备 | 有线电信设备 | 1 | 台 | tCO₂e/台 | carbonstop-ccdb-1381776767973120 |
| 机械设备 | 照明设备 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776374789888 |
| 机械设备 | 纺织机械 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776305223424 |
| 机械设备 | 食品机械设备 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776308532992 |
| 林业碳汇 | 燃烧的干物质 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704587642860288 |
| 水泥 | 水泥砂浆 | 1 | m³ | kgCO₂e/m³ | carbonstop-ccdb-1381767594800896 |
| 海上交通 | 散货船，平均 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1476787179813120 |
| 海上交通 | 普通货船，平均 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1476787209730304 |
| 海上交通 | 杂货船 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1337961692359680 |
| 海上交通 | 滚装船 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1337962239552512 |
| 海上交通 | 货船（运载冷藏货物） | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1337962243091456 |
| 海上交通 | 货船（运载车辆） | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1337961717525504 |
| 海上交通 | 轮船 | 1 | 吨公里 | gCO₂e/吨公里 | carbonstop-ccdb-1381774894855936 |
| 海上交通 | 集装箱船，平均 | 1 | 吨公里 | kgCO₂e/吨公里 | carbonstop-ccdb-1476787239713024 |
| 热力 | 区域热力和蒸汽分配（5%损耗） | 1 | kWh | kgCO₂e/kWh | carbonstop-ccdb-1337960171990016 |
| 热力 | 热力 | 1 | MJ | tCO₂e/MJ | carbonstop-ccdb-1381778863159040 |
| 热力 | 热力和蒸汽 | 1 | kWh | kgCO₂e/kWh | carbonstop-ccdb-1337959893724160 |
| 热力 | 热力燃烧获取排放因子 | 1 | MJ | kgCO₂e/MJ | carbonstop-ccdb-1584395203277312 |
| 热力 | 英国区域性热力和蒸汽 | 1 | kWh | kgCO₂e/kWh | carbonstop-ccdb-1584418876486144 |
| 热力 | 英国厂内热力和蒸汽 | 1 | kWh | kgCO₂e/kWh | carbonstop-ccdb-1584418878255616 |
| 煤炭 | 一般煤油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446350300928 |
| 煤炭 | 其他洗煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446333785856 |
| 煤炭 | 其他石油制品 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446355150592 |
| 煤炭 | 其它煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446381102848 |
| 煤炭 | 原油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446341158656 |
| 煤炭 | 型煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446336308992 |
| 煤炭 | 天然气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446369306368 |
| 煤炭 | 密闭电石炉气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446378809088 |
| 煤炭 | 无烟煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446324643584 |
| 煤炭 | 柴油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446348072704 |
| 煤炭 | 汽油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446345713408 |
| 煤炭 | 洗精煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446331492096 |
| 煤炭 | 液化天然气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446366816000 |
| 煤炭 | 液化石油气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446364522240 |
| 煤炭 | 炼厂干气 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446362228480 |
| 煤炭 | 烟煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446326806272 |
| 煤炭 | 焦油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446357673728 |
| 煤炭 | 焦炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446371469056 |
| 煤炭 | 焦炭 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446338635520 |
| 煤炭 | 燃料油 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446343321344 |
| 煤炭 | 石油焦 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446352791296 |
| 煤炭 | 粗苯 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446359869184 |
| 煤炭 | 褐煤 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1382446329165568 |
| 煤炭 | 转炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446376318720 |
| 煤炭 | 高炉煤气 | 1 | 万Nm³ | kgCO₂e/万Nm³ | carbonstop-ccdb-1382446374057728 |
| 玻璃 | 平面显示器用玻璃基板 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381767113307904 |
| 玻璃 | 玻璃纤维及同类产品 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1584397114962432 |
| 电力 | 电力 | 1 | MWh | tCO₂e/MWh | carbonstop-ccdb-1609534350883840 |
| 电力 | 电力：东北 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423353315840 |
| 电力 | 电力：华东 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423356428800 |
| 电力 | 电力：华中 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423357936128 |
| 电力 | 电力：华北 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423354855936 |
| 电力 | 电力：南方 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423359508992 |
| 电力 | 电力：西北 | 1 | kWh | tCO₂e/kWh | carbonstop-ccdb-1584423361049088 |
| 电脑 | 16 英寸 MacBook Pro-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496484438637824 |
| 电脑 | Acer 15.6英寸笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704585990700032 |
| 电脑 | Latitude E6400商务笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586675010560 |
| 电脑 | Latitude E6440商务笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586656283648 |
| 电脑 | Latitude E6540商务笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586665565184 |
| 电脑 | Latitude E7240商务笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586684316672 |
| 电脑 | Latitude E7440商务笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704586693680128 |
| 电脑 | MacBook Air-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1476794359412992 |
| 电脑 | ThinkBook 15 2nd Gen AMD/Prestigio 6-15-全生命周期 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1496483269672192 |
| 电脑 | 个人电脑 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381776415749888 |
| 电脑 | 戴尔笔记本电脑 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704585411206144 |
| 电脑 | 电脑显示器 | 1 | t | tCO₂e/t | carbonstop-ccdb-1584395373703680 |
| 电脑 | 笔记本电脑 | 1 | 台 | kgCO₂e/台 | carbonstop-ccdb-1381767974582016 |
| 造纸和纸制品 | AB楞纸箱 | 1 | ㎡ | kgCO₂e/㎡ | carbonstop-ccdb-1381768338241280 |
| 造纸和纸制品 | 牛皮纸 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381767099184896 |
| 造纸和纸制品 | 纸和纸板：纸板 | 1 | t | kgCO₂e/t | carbonstop-ccdb-1337962906184704 |
| 造纸和纸制品 | 纸张 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775721461504 |
| 造纸和纸制品 | 纸板 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775519479552 |
| 钢铁 | 烙铁合金 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426642799616 |
| 钢铁 | 生铁 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426637687808 |
| 钢铁 | 直接还原铁 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426639358976 |
| 钢铁 | 粗钢 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426647780352 |
| 钢铁 | 钼铁合金 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426644438016 |
| 钢铁 | 镍铁合金 | 1 | t | tCO₂e/t | carbonstop-ccdb-1279426641095680 |
| 陆上交通 | 刚性重型货车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959555230720 |
| 陆上交通 | 厢式货车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959501097984 |
| 陆上交通 | 大型家庭车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959229975552 |
| 陆上交通 | 机器脚踏车 | 1 | 人公里 | kgCO₂e/人公里 | carbonstop-ccdb-1381767066121984 |
| 陆上交通 | 柴油货车 | 1 | km | kgCO₂e/km | carbonstop-ccdb-1496473355255040 |
| 陆上交通 | 汽油货车 | 1 | km | kgCO₂e/km | carbonstop-ccdb-1496473350077696 |
| 陆上交通 | 紧凑型家庭车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959226469376 |
| 陆上交通 | 载客汽车 | 1 | km | tCO₂e/km | carbonstop-ccdb-1704587623764736 |
| 陆上交通 | 载货汽车（含挂车） | 1 | km | tCO₂e/km | carbonstop-ccdb-1704587601629952 |
| 陆上交通 | 运动型实用车辆SUV | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959244426240 |
| 陆上交通 | 重型货车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959580625920 |
| 陆上交通 | 铰链式重型货车 | 1 | 英里 | kgCO₂e/英里 | carbonstop-ccdb-1337959569746944 |
| 陶瓷 | 陶瓷，石制品 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1584425587700224 |
| 食品、烟酒、茶 | 冷冻海鲜 | 1 | t | tCO₂e/t | carbonstop-ccdb-1381777155618560 |
| 食品、烟酒、茶 | 冷冻鱼贝类 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775218276096 |
| 食品、烟酒、茶 | 刀削面 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381768526722816 |
| 食品、烟酒、茶 | 可乐 | 1 | 瓶 | kgCO₂e/瓶 | carbonstop-ccdb-1381768472688384 |
| 食品、烟酒、茶 | 咖喱酱 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768316712704 |
| 食品、烟酒、茶 | 啤酒 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775404857088 |
| 食品、烟酒、茶 | 奶茶 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381767887976192 |
| 食品、烟酒、茶 | 奶酪 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775078520576 |
| 食品、烟酒、茶 | 尼古丁 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1704587561188352 |
| 食品、烟酒、茶 | 意面 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381768529213184 |
| 食品、烟酒、茶 | 有机小麦粉 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768574727936 |
| 食品、烟酒、茶 | 柳橙汁 | 1 | 瓶 | kgCO₂e/瓶 | carbonstop-ccdb-1381768475178752 |
| 食品、烟酒、茶 | 柴鱼花-鲣鱼 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768335619840 |
| 食品、烟酒、茶 | 柿饼 | 1 | 盒 | kgCO₂e/盒 | carbonstop-ccdb-1381768546612992 |
| 食品、烟酒、茶 | 海鲜罐头 | 1 | t | tCO₂e/t | carbonstop-ccdb-1381777165711104 |
| 食品、烟酒、茶 | 淀粉 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775335847680 |
| 食品、烟酒、茶 | 清酒 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775607789312 |
| 食品、烟酒、茶 | 牛 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775106111232 |
| 食品、烟酒、茶 | 猪肉 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768610019072 |
| 食品、烟酒、茶 | 畜产品罐头 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775245408000 |
| 食品、烟酒、茶 | 糕饼 | 1 | t | tCO₂e/t | carbonstop-ccdb-1381777190483712 |
| 食品、烟酒、茶 | 糖 | 2 | kg, 百万日元 | kgCO₂e/kg, tCO₂e/百万日元 | carbonstop-ccdb-1704587983248384, carbonstop-ccdb-1381775332538112 |
| 食品、烟酒、茶 | 素火腿 | 1 | 条 | kgCO₂e/条 | carbonstop-ccdb-1381768042149632 |
| 食品、烟酒、茶 | 红茶 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381767895414528 |
| 食品、烟酒、茶 | 经典台湾啤酒 | 1 | 箱 | kgCO₂e/箱 | carbonstop-ccdb-1381767944238848 |
| 食品、烟酒、茶 | 绿茶 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381767902918400 |
| 食品、烟酒、茶 | 芝麻油 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768480257792 |
| 食品、烟酒、茶 | 调味料 | 1 | 百万日元 | tCO₂e/百万日元 | carbonstop-ccdb-1381775349675776 |
| 食品、烟酒、茶 | 豆浆 | 1 | 盒 | kgCO₂e/盒 | carbonstop-ccdb-1381767885453056 |
| 食品、烟酒、茶 | 面包 | 2 | t, 百万日元 | tCO₂e/t, tCO₂e/百万日元 | carbonstop-ccdb-1381777187272448, carbonstop-ccdb-1381775282632448 |
| 食品、烟酒、茶 | 面条 | 1 | kg | kgCO₂e/kg | carbonstop-ccdb-1381768518792960 |
| 食品、烟酒、茶 | 面粉 | 1 | kg | gCO₂e/kg | carbonstop-ccdb-1381767923529472 |
| 食品、烟酒、茶 | 面粉研磨 | 1 | t | tCO₂e/t | carbonstop-ccdb-1381777180423936 |
| 食品、烟酒、茶 | 高山乌龙茶 | 1 | 包 | kgCO₂e/包 | carbonstop-ccdb-1381768564307712 |
| 食品、烟酒、茶 | 鲜蛋 | 1 | 颗 | kgCO₂e/颗 | carbonstop-ccdb-1381767473788672 |

## Common Aliases

| User wording | Query activity hints |
| --- | --- |
| 外购电力、用电、电量、购电、kWh、度电 | electricity / purchased_electricity |
| 天然气、燃气、natural gas、m3、立方米 | natural_gas / stationary_combustion |
| 柴油、diesel | diesel / stationary_combustion |
| 汽油、gasoline | gasoline / stationary_combustion |
| 液化石油气、LPG | lpg / stationary_combustion |
| 煤、原煤、coal | coal / stationary_combustion |
| 蒸汽、外购蒸汽、steam | steam / purchased_energy |
| 自来水、用水、water | water / water_supply |
| 制冷剂、冷媒、R410A、R134a | refrigerant; current registry may not contain direct refrigerant factors |

## Known Gaps

- If `carbon_factor_lookup` returns no hit for a listed alias, answer that the current local registry lacks a calculation-ready factor for that activity.
- Refrigerants such as R410A/R134a are recognized as requested activities, but direct GWP/factor records may be absent in the current seed registry.
