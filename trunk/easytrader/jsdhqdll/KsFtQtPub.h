//创建:钱彬
//日期:20061115
//描述:期货v6对外公布的行情接口，已经预留了深度行情的字段

#ifndef __KSFTQTPUB_H
#define __KSFTQTPUB_H
// The following ifdef block is the standard way of creating macros which make exporting 
// from a DLL simpler. All files within this DLL are compiled with the KSFTQTPUB_EXPORTS
// symbol defined on the command line. this symbol should not be defined on any project
// that uses this DLL. This way any other project whose source files include this file see 
// KSFTQTPUB_API functions as being imported from a DLL, wheras this DLL sees symbols
// defined with this macro as being exported.
#ifdef KSFTQTPUB_EXPORTS
#define KSFTQTPUB_API __declspec(dllexport)
#else
#define KSFTQTPUB_API __declspec(dllimport)
#endif

const int MAX_QUOTA_STATUS_LEN = 2;
const int MAX_DATE_LEN = 9;
const int MAX_EXCHCODE_LEN = 6;
const int MAX_VARI_LEN = 32;
const int MAX_HQTYPE_LEN = 2;
#ifndef WIN32
#ifndef __GNUC__
#define __PACKED__
#pragma options align=packed
#else
#define __PACKED__	__attribute__ ((packed))
#pragma pack(push,4)
#endif
#else
#define __PACKED__ 
#pragma pack(push,4)
#endif

typedef struct ksftquota_pubdata_item_tag
{
	int	contract_id;				//由交易品种和交割期算出来的id,对应：id号;
	int	upd_serial;				//行情更新序号，对应：序号
	int	upd_date;				//行情日期,格式：YYYYMMDD
	int	pre_upd_date;				//行情上次更新日期(保留)
	int	pre_upd_serial;				//上次更新时的序号(保留)
	char	sys_recv_time[MAX_DATE_LEN];		//行情服务器收到行情的时间，行情服务器唯一维护，格式：HH:MM:SS

	char	exchCode[MAX_EXCHCODE_LEN];		//交易所代码
	char	varity_code[MAX_VARI_LEN];		//品种代码
	char	deliv_date[MAX_DATE_LEN];		//交割期
	char	chgStatus[MAX_QUOTA_STATUS_LEN];	//对应：状态
							//1-2bit表示：买入;3-4bit表示：卖出;
							//5-6bit表示：最新;7-8bit不用;
							//00->新行情    01->低于以前的行情
							//11->高于以前的行情    00->与以前相平
	
	double	openPrice;				//开盘价
	double	lastPrice;				//最新价
	double	highestPrice;				//最高价
	double	lowestPrice;				//最低价
	int	doneVolume;				//成交量
	double	chgPrice;				//涨跌
	double	upperLimitPrice;			//涨停板
	double	lowerLimitPrice;			//跌停板
	double	hisHighestPrice;			//历史最高价
	double	hisLowestPrice;				//历史最低价
	int	openInterest;				//净持仓
	double	preSettlePrice;				//昨日结算
	double	preClosePrice;				//昨日收盘
	double	settlePrice;				//今日结算
	double	turnover;				//成交金额
	//20061208新增,qbin
	int	preOpenInterest;			//昨日持仓量
	double	closePrice;				//今日收盘
	double	preDelta;				//昨虚实度
	double	currDelta;				//今虚实度
	
	
	double	bidPrice1;				//买入价1
	int	bidVolume1;				//买入量1
	double	bidPrice2;				//买入价2
	int	bidVolume2;				//买入量2
	double	bidPrice3;				//买入价3
	int	bidVolume3;				//买入量3
	double	bidPrice4;				//买入价4
	int	bidVolume4;				//买入量4
	double	bidPrice5;				//买入价5
	int	bidVolume5;				//买入量5

	double	askPrice1;				//卖出价1
	int	askVolume1;				//卖出量1
	double	askPrice2;				//卖出价2
	int	askVolume2;				//卖出量2
	double	askPrice3;				//卖出价3
	int	askVolume3;				//卖出量3
	double	askPrice4;				//卖出价4
	int	askVolume4;				//卖出量4
	double	askPrice5;				//卖出价5
	int	askVolume5;				//卖出量5

	char cmbtype[MAX_HQTYPE_LEN];   //‘0’或NULL:普通行情
									//‘1’：组合套利行情
	//20080514
	int derive_bidlot;   //买推导量   组合买入数量
	int derive_asklot;   //卖推导量   组合卖出数量
	
}KSFT_QUOTA_PUBDATA_ITEM;

#ifndef WIN32
#ifndef __GNUC__
#pragma options align=reset
#else
#pragma pack(pop)
#endif
#else
#pragma pack(pop)
#endif


//功能：启动行情接收
//参数:
//udpPort[in]:接收udp行情的广播端口
//errorMsg[out]:错误消息，缓冲区大小必须大于等于256个字节
//返回:
//true:成功
//false:失败，可以从errorMsg中获取错误原因
//特别说明:在程序启动的时候调用一次就可以了
KSFTQTPUB_API bool WINAPI KSFTHQPUB_Start(unsigned short udpPort, char* errorMsg);

//功能：关闭行情接收,并且释放内部资源
KSFTQTPUB_API void WINAPI KSFTHQPUB_Stop();

//功能：获取以KSFT_QUOTA_PUBDATA_ITEM数组存放的行情信息,可能一次返回一条或者多条行情
//参数:
//dataBuf[out]:存放KSFT_QUOTA_PUBDATA_ITEM格式的行情数组缓冲
//bufSize[in]:KSFT_QUOTA_PUBDATA_ITEM数组大小(以字节为单位)
//timeOut[in]:超时时间,单位毫秒
//errorMsg[out]:错误消息，缓冲区大小必须大于等于256个字节
//返回:
//0:接收超时,没有行情数据
//>0:表示dataBuf中存储了KSFT_QUOTA_PUBDATA_ITEM结构的行情数据的个数
//<0:调用错误，可以通过errorMsg获得错误信息
//特别说明:在KSFTHQPUB_Start成功后，不断调用来获取行情信息，一般建议单独开一个线程获取行情信息

KSFTQTPUB_API int WINAPI KSFTHQPUB_GetQuota(unsigned char* dataBuf, int bufSize, int timeOut, char* errorMsg);

#endif
