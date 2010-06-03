//����:Ǯ��
//����:20061115
//����:�ڻ�v6���⹫��������ӿڣ��Ѿ�Ԥ�������������ֶ�

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
	int	contract_id;				//�ɽ���Ʒ�ֺͽ������������id,��Ӧ��id��;
	int	upd_serial;				//���������ţ���Ӧ�����
	int	upd_date;				//��������,��ʽ��YYYYMMDD
	int	pre_upd_date;				//�����ϴθ�������(����)
	int	pre_upd_serial;				//�ϴθ���ʱ�����(����)
	char	sys_recv_time[MAX_DATE_LEN];		//����������յ������ʱ�䣬���������Ψһά������ʽ��HH:MM:SS

	char	exchCode[MAX_EXCHCODE_LEN];		//����������
	char	varity_code[MAX_VARI_LEN];		//Ʒ�ִ���
	char	deliv_date[MAX_DATE_LEN];		//������
	char	chgStatus[MAX_QUOTA_STATUS_LEN];	//��Ӧ��״̬
							//1-2bit��ʾ������;3-4bit��ʾ������;
							//5-6bit��ʾ������;7-8bit����;
							//00->������    01->������ǰ������
							//11->������ǰ������    00->����ǰ��ƽ
	
	double	openPrice;				//���̼�
	double	lastPrice;				//���¼�
	double	highestPrice;				//��߼�
	double	lowestPrice;				//��ͼ�
	int	doneVolume;				//�ɽ���
	double	chgPrice;				//�ǵ�
	double	upperLimitPrice;			//��ͣ��
	double	lowerLimitPrice;			//��ͣ��
	double	hisHighestPrice;			//��ʷ��߼�
	double	hisLowestPrice;				//��ʷ��ͼ�
	int	openInterest;				//���ֲ�
	double	preSettlePrice;				//���ս���
	double	preClosePrice;				//��������
	double	settlePrice;				//���ս���
	double	turnover;				//�ɽ����
	//20061208����,qbin
	int	preOpenInterest;			//���ճֲ���
	double	closePrice;				//��������
	double	preDelta;				//����ʵ��
	double	currDelta;				//����ʵ��
	
	
	double	bidPrice1;				//�����1
	int	bidVolume1;				//������1
	double	bidPrice2;				//�����2
	int	bidVolume2;				//������2
	double	bidPrice3;				//�����3
	int	bidVolume3;				//������3
	double	bidPrice4;				//�����4
	int	bidVolume4;				//������4
	double	bidPrice5;				//�����5
	int	bidVolume5;				//������5

	double	askPrice1;				//������1
	int	askVolume1;				//������1
	double	askPrice2;				//������2
	int	askVolume2;				//������2
	double	askPrice3;				//������3
	int	askVolume3;				//������3
	double	askPrice4;				//������4
	int	askVolume4;				//������4
	double	askPrice5;				//������5
	int	askVolume5;				//������5

	char cmbtype[MAX_HQTYPE_LEN];   //��0����NULL:��ͨ����
									//��1���������������
	//20080514
	int derive_bidlot;   //���Ƶ���   �����������
	int derive_asklot;   //���Ƶ���   �����������
	
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


//���ܣ������������
//����:
//udpPort[in]:����udp����Ĺ㲥�˿�
//errorMsg[out]:������Ϣ����������С������ڵ���256���ֽ�
//����:
//true:�ɹ�
//false:ʧ�ܣ����Դ�errorMsg�л�ȡ����ԭ��
//�ر�˵��:�ڳ���������ʱ�����һ�ξͿ�����
KSFTQTPUB_API bool WINAPI KSFTHQPUB_Start(unsigned short udpPort, char* errorMsg);

//���ܣ��ر��������,�����ͷ��ڲ���Դ
KSFTQTPUB_API void WINAPI KSFTHQPUB_Stop();

//���ܣ���ȡ��KSFT_QUOTA_PUBDATA_ITEM�����ŵ�������Ϣ,����һ�η���һ�����߶�������
//����:
//dataBuf[out]:���KSFT_QUOTA_PUBDATA_ITEM��ʽ���������黺��
//bufSize[in]:KSFT_QUOTA_PUBDATA_ITEM�����С(���ֽ�Ϊ��λ)
//timeOut[in]:��ʱʱ��,��λ����
//errorMsg[out]:������Ϣ����������С������ڵ���256���ֽ�
//����:
//0:���ճ�ʱ,û����������
//>0:��ʾdataBuf�д洢��KSFT_QUOTA_PUBDATA_ITEM�ṹ���������ݵĸ���
//<0:���ô��󣬿���ͨ��errorMsg��ô�����Ϣ
//�ر�˵��:��KSFTHQPUB_Start�ɹ��󣬲��ϵ�������ȡ������Ϣ��һ�㽨�鵥����һ���̻߳�ȡ������Ϣ

KSFTQTPUB_API int WINAPI KSFTHQPUB_GetQuota(unsigned char* dataBuf, int bufSize, int timeOut, char* errorMsg);

#endif
