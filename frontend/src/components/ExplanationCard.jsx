const ExplanationCard = ({ explanation }) => {
  return (
    <div className="bg-box-primary rounded-3xl p-8">
      <p className="heading-section text-white mb-6">Explanation</p>
      <p className="text-white text-base font-inter leading-relaxed">
        {explanation}
      </p>
    </div>
  );
};

export default ExplanationCard;