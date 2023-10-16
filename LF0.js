import AWS from 'aws-sdk';
const sqs = new AWS.SQS();

export const handler = async (event) => {
 
  // successful return 
  const resp = {
    statusCode: 200,
    sessionState: event.sessionState || {}, // Ensure sessionState exists and initialize if not
  };
  
  // checking for next state
  if (event.proposedNextState) {
    resp.sessionState.dialogAction = event.proposedNextState.dialogAction;
  
  // if done, proceed on to sending Lex's response to the SQS 
  } else {
    resp.sessionState.dialogAction = { type: "Close" };

    try {
      
      const params = {
        QueueUrl: 'https://sqs.us-east-1.amazonaws.com/439569526489/messages',
        MessageBody: JSON.stringify(event)
      };

      const response = await sqs.sendMessage(params).promise();
      return resp;
  
    } catch (error) {
      console.error("Error sending message to SQS:", error);
  
      return {
        statusCode: 500,
        body: { error: "Error sending message to SQS" }
      };
    }
  }
  return resp;
};